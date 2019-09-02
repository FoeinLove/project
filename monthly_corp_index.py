#每月第一天执行
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import time

sc = SparkContext()
spark = SparkSession(sc)

i = time.strftime('%Y%m',time.localtime(time.time() - 3600 * 24 ))
x=['00224629D5F9','2851321038F7','285132051A23','2851320FD3ED','00224628A657','285132102EE4','285132102EC4','002246297C14','002246297BF6','0022461F7D52','0022462987DB']
for n in x:
	try:
		df = spark.read.csv('/user/maxnet/ian/corp_index_1/%s_%s*'%(n,i),header=True)
		df = df.select('time','sn',col('count').cast('float').alias('mac_count'),col('avg_ht').cast('float'),col('avg_bi').cast('float'),col('std_ht').cast('float'),col('std_bi').cast('float'),col('qingxu').cast('float'))
		
		tmp1 = [{'sn': '%s'%(n), 'chengzhang1': df.approxQuantile('mac_count', [0.75], 0)[0] / df.approxQuantile('mac_count', [1.0], 0)[0]}]
		tmp1 = spark.createDataFrame(tmp1).select('sn',round('chengzhang1',3 ).alias('chengzhang1'))
		tmp1 = tmp1.withColumnRenamed('sn','sn1')
		tmp2 = [{'sn': '%s'%(n), 'chengzhang2': df.approxQuantile('avg_ht', [0.75], 0)[0] / df.approxQuantile('avg_ht', [1.0], 0)[0]}]
		tmp2 = spark.createDataFrame(tmp2).select('sn',round('chengzhang2',3 ).alias('chengzhang2'))
		tmp2 = tmp2.withColumnRenamed('sn','sn2')
		tmp = tmp1.join(tmp2,tmp1.sn1 == tmp2.sn2,how='inner')
		tmp = tmp.select('sn1','chengzhang1','chengzhang2')
		tmp = tmp.withColumn('chengzhang',round((tmp.chengzhang1+tmp.chengzhang2)/2,3))
		tmp = tmp.select('sn1','chengzhang').withColumnRenamed('sn1','sn_chengzhang')

		wending = df.groupby('sn').agg(round(stddev('qingxu'),3)).withColumnRenamed('round(stddev_samp(qingxu), 3)','wending')
		wending = wending.withColumnRenamed('sn','sn_wending')

		qinmian = df.groupby('sn').agg(round(avg('qingxu'),3)).withColumnRenamed('round(avg(qingxu), 3)','qinmian')
		qinmian = qinmian.withColumnRenamed('sn','sn_qinmian')
		
		combine = tmp.join(wending,tmp.sn_chengzhang==wending.sn_wending,how='inner')
		combine = combine.join(qinmian,combine.sn_wending==qinmian.sn_qinmian,how='inner')
		combine= combine.select('sn_chengzhang','qinmian','chengzhang','wending').withColumnRenamed('sn_chengzhang','sn').withColumn('date',lit('%s'%(i)))
		
		combine = combine.repartition(1)
		combine.write.csv('/user/maxnet/ian/corp_index_1/month_index/%s_%s' %(n,i),header=True, compression='gzip',mode='overwrite')
	except:
		pass    

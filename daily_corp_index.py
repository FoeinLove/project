#每天执行
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import time

sc = SparkContext()
spark = SparkSession(sc)

i = time.strftime('%Y%m%d',time.localtime(time.time() - 3600 * 24 ))
x=['00224629D5F9','2851321038F7','285132051A23','2851320FD3ED','00224628A657','285132102EE4','285132102EC4','002246297C14','002246297BF6','0022461F7D52','0022462987DB']
for n in x:
	try:
		df = spark.read.parquet('/user/hive/warehouse/cld.db/app/day=%s*' %(i))
        
		from pyspark.sql.functions import from_unixtime,to_date
		df = df.select('sn','mac','realAppID','hitTimes','bytesIn','period',from_unixtime('time').alias('ts'))
		df = df.withColumn('time',to_date('ts'))
		df = df.drop('ts').filter(df.period == 60).distinct().dropna()
		df = df.select('time','sn','mac','realAppID','hitTimes','bytesIn')
		yjjd = df.filter(df.sn == '%s'%(n)).distinct().dropna()
		dd = yjjd.select('sn','mac','time').distinct().groupby('time','sn').count()

		mean = yjjd.groupBy('sn').avg('hitTimes', 'bytesIn')
		mean = mean.withColumnRenamed('avg(hitTimes)','avg_ht').withColumnRenamed('avg(bytesIn)','avg_bi')
		mean = mean.withColumnRenamed('sn','sn1')

		std = yjjd.groupBy('sn').agg({'hitTimes':'stddev', 'bytesIn':'stddev'})
		std = std.withColumnRenamed('stddev(hitTimes)','std_ht').withColumnRenamed('stddev(bytesIn)','std_bi')
		std = std.withColumnRenamed('sn','sn2')

		df = dd.join(mean,dd.sn == mean.sn1,how='inner')
		df = df.join(std,df.sn == std.sn2,how='inner')
		df = df.selectExpr('time','sn','count','round(avg_ht,1)','round(avg_bi,1)','round(std_ht,1)','round(std_bi,1)')

		df = df.withColumnRenamed('round(avg_ht, 1)','avg_ht').\
		withColumnRenamed('round(avg_bi, 1)','avg_bi').\
		withColumnRenamed('round(std_ht, 1)','std_ht').\
		withColumnRenamed('round(std_bi, 1)','std_bi')

		app = spark.read.csv('/user/maxnet/ian/demo/app_id.csv',header=True,encoding='gb18030')
		yjjd = yjjd.join(app,yjjd.realAppID == app.app_id,how='inner').select('sn','realAppID','ch_name','group_ch')
		yjjd = yjjd.distinct().dropna()
		yjjd_count = yjjd.count()
		shipin = yjjd.filter(yjjd.group_ch == '影音试听').count()
		gouwu = yjjd.filter(yjjd.group_ch == '网络购物').count()
		youxi = yjjd.filter(yjjd.group_ch == '网络游戏').count()
		ddd = [{'sn': '%s'%(n), 'qingxu': 0 if yjjd_count == 0 else (yjjd_count-shipin-gouwu-youxi)/yjjd_count}]
		ddd = spark.createDataFrame(ddd).select('sn',bround('qingxu', 2).alias('qingxu'))
		ddd= ddd.withColumnRenamed('sn','sn1')
		df = df.join(ddd,df.sn == ddd.sn1,how='inner')
		df = df.select('time','sn','count','avg_ht','avg_bi','std_ht','std_bi','qingxu')
		df = df.repartition(1)
		df.write.csv('/user/maxnet/ian/corp_index_1/%s_%s' %(n,i),header=True, compression='gzip',mode='overwrite')
	except:
		pass 

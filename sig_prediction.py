from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import * 
from pyspark.ml.classification import RandomForestClassificationModel
import time 

sc = SparkContext()
spark = SparkSession(sc)

i = time.strftime('%Y%m%d',time.localtime(time.time()))

try:
    m = RandomForestClassificationModel.load('/data/user/hive/warehouse/ian/model/m')
    
    d = spark.read.csv('/user/maxnet/database/sig.db/data_visual_unknown/*',sep='\x01')
    d1 = d.select('_c2').withColumnRenamed('_c2','val').distinct().dropna()
    d1 = d1.withColumn('f1',length(col('val')))

    d1 = d1.withColumn('f2',when(d1.val.startswith('A')|d1.val.startswith('B')|d1.val.startswith('C')                             |d1.val.startswith('D')|d1.val.startswith('E')|d1.val.startswith('F')                             |d1.val.startswith('G')|d1.val.startswith('H')|d1.val.startswith('I')                             |d1.val.startswith('J')|d1.val.startswith('K')|d1.val.startswith('L')                             |d1.val.startswith('M')|d1.val.startswith('N')|d1.val.startswith('O')                             |d1.val.startswith('P')|d1.val.startswith('Q')|d1.val.startswith('R')                             |d1.val.startswith('S')|d1.val.startswith('T')|d1.val.startswith('U')                             |d1.val.startswith('V')|d1.val.startswith('W')|d1.val.startswith('X')                             |d1.val.startswith('Y')|d1.val.startswith('Z'),1).otherwise(0))

    import re

    num_regex = re.compile(r'[0-9]') 
    xiaoxiezimu_regex = re.compile(r'[a-z]')
    daxiezimu_regex = re.compile(r'[A-Z]')


    from pyspark.sql.functions import udf
    num = udf(lambda x: len(num_regex.findall(x)))
    xiaoxie = udf(lambda x: len(xiaoxiezimu_regex.findall(x)))
    daxie = udf(lambda x: len(daxiezimu_regex.findall(x)))

    d1 = d1.withColumn('f3',num('val'))
    d1 = d1.withColumn('f4',xiaoxie('val'))
    d1 = d1.withColumn('f5',daxie('val'))

    def xiahuaxian_count(s):
        xiahuaxian_counts=0
        for c in s:
            xiahuaxian_split_list = c.split('_')
            xiahuaxian_counts += len(xiahuaxian_split_list) - 1
        return xiahuaxian_counts


    def zhonghuaxian_count(s):
        zhonghuaxian_counts=0
        for c in s:
            zhonghuaxian_split_list = c.split('-')
            zhonghuaxian_counts += len(zhonghuaxian_split_list) - 1
        return zhonghuaxian_counts

    def maohao_count(s):
        maohao_counts=0
        for c in s:
            maohao_split_list = c.split(':')
            maohao_counts += len(maohao_split_list) - 1
        return maohao_counts

    def teshu_count(s):
        teshu_counts=0
        a_counts=0
        b_counts=0
        c_counts=0
        for c in s:
            a_split_list = c.split('_')
            a_counts += len(a_split_list) - 1
        
            b_split_list = c.split('-')
            b_counts += len(b_split_list) - 1
        
            c_split_list = c.split(':')
            c_counts += len(c_split_list) - 1
        
            teshu_counts = a_counts + b_counts + c_counts
        return teshu_counts
        
    def space_count(s):
        space_counts=0
        for c in s:
            space_split_list = c.split(' ')
            space_counts += len(space_split_list) - 1
        return space_counts

    teshu = udf(lambda x: teshu_count(x))
    kongge = udf(lambda x: space_count(x))


    d1 = d1.withColumn('f6',teshu('val'))
    d1 = d1.withColumn('f7',kongge('val'))


    d1 = d1.select('val',col('f1').cast('float'),col('f2').cast('float'),col('f3').cast('float'),col('f4').cast('float'),col('f5').cast('float'),col('f6').cast('float'),col('f7').cast('float'))

    from pyspark.ml.feature import VectorAssembler

    vec = VectorAssembler(inputCols=['f1','f2','f3','f4','f5','f6','f7'],outputCol='features')
    unknow = vec.transform(d1)

    t = m.transform(unknow)

    from pyspark.sql.types import DoubleType
    unlist = udf(lambda x: float(list(x)[1]), DoubleType())

    total = t.select('val',unlist('probability').alias('probability'),'prediction').filter(~t.val.contains('unknown')).filter(~t.val.contains('empty')).filter(~t.val.contains('NONE')).filter(~t.val.contains('none')).filter(~t.val.contains('N/A')).filter(~t.val.contains('normal')).filter(~t.val.contains('anonymous')).filter(~t.val.contains('null'))

    total_hdfs = total.repartition(1)

    total_hdfs.write.mode('overwrite').csv('hdfs:///user/maxnet/data/prediction/p_%s.csv' %(i),header=True,compression='gzip')
except:
    pass


# -*- coding: utf-8 -*-
"""DS503_Project3_Q2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rH9bRHKEoD4703EMgYOZAP5uem95zacP

# Setup of Spark Environment
"""

!apt-get install openjdk-8-jdk-headless -qq > /dev/null
!wget -q http://archive.apache.org/dist/spark/spark-3.1.1/spark-3.1.1-bin-hadoop3.2.tgz
!tar xf spark-3.1.1-bin-hadoop3.2.tgz
!pip install -q findspark

import os
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
os.environ["SPARK_HOME"] = "/content/spark-3.1.1-bin-hadoop3.2"

"""# Spark-RDDs (Grid Cells of High Relative-Density Index)

## Report the TOP 50 grid cells w.r.t Relative-Density Index

Steps:

1. Import points dataset as dataframe and set schema *(x_val, y_val)*

2. Rename column headers

3. Assign point's current grid

    a.   x_grid = ceiling (x_val / 20)

    b.   y_grid = [ceiling (x_val / 20) - 1] * 500

    c.   curr_grid = x_grid + y_grid

4. Assign neighbors

    a. n_1 = curr_grid + 500 - 1

    b. n_2 = curr_grid + 500

    c. n_3 = curr_grid + 500 + 1

    d. n_4 = curr_grid + 1

    e. n_5 = curr_grid - 500 + 1

    f. n_6 = curr_grid - 500

    g. n_7 = curr_grid - 500 - 1

    h. n_8 = curr_grid - 1

5. Check if neighbor is valid

    a. If x_grid = 1, then no n_1, n_8, n_7

    b. If curr_grid <= 500, then no n_7, n_6, n_5

    c. If curr_grid % 500 == 0, then no n_3, n_4, n_5

    d. if curr_grid >= 249,951, then no n_1, n_2, n_3

6. Group By ID & count for curr_grid & all neighbors

7. Calculate the Relative-Density Index *(rel_density)* for curr_grid:

    *rel_density = curr_grid.count / avg(n_1.count, n_2.count, n_3.count, n_4.count, n_5.count, n_6.count, n_7.count, n_8.count)*

8. Order By rel_density and limit 50

## Imports & Setup
"""

# Imports & setup
import findspark
findspark.init()
from pyspark.sql import SparkSession

# Start Spark Session
spark = SparkSession.builder.master("local[*]").config("spark.sql.analyzer.failAmbiguousSelfJoin", False).getOrCreate()
spark.conf.set("spark.sql.repl.eagerEval.enabled", True)
spark.conf.set("spark.sql.broadcastTimeout", "1800s")  # Set timeout to 1800 seconds (30 minutes)
spark

# Import functions to use later
from pyspark.sql.functions import col, sum, avg, min, max, count, ceil, when, lit, coalesce

"""## Step 1: Import points dataset as dataframe and set schema (x_val, y_val)"""

# Import test points dataset with inferred schema
points_df = spark.read.csv("Points.txt", header=False, inferSchema=True)
points_df.show()

"""## Step 2: Add column headers"""

# Add column headers x_val, y_val
points_column_headers = ["x_val", "y_val"]
for i, col_name in enumerate(points_column_headers):
    points_df = points_df.withColumnRenamed("_c" + str(i), col_name)
points_df.printSchema()

# Start with P (points) as a dataframe
P = points_df

"""## Step 3: Assign point's current grid

1. x_grid = ceiling (x_val / 20)

2. y_grid = [ceiling (x_val / 20) - 1] * 500

3. curr_grid = x_grid + y_grid
"""

# Assign current grid for each point

# import type of output & udf
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import udf
from math import ceil

# Define udf to get grid x
def get_x_grid(x):
    return ceil(x / 20)

get_x_grid_udf = udf(get_x_grid, IntegerType())

# Define udf to get grid y
def get_y_grid(x):
    if x == 0:
        return 0  # Return 0 if x is 0
    else:
        return (ceil(x / 20) - 1) * 500

get_y_grid_udf = udf(get_y_grid, IntegerType())

# Define udf to get grid
def get_grid(x, y):
    return x + y

get_grid_udf = udf(get_grid, IntegerType())

# Apply udfs to get grid information for each point
P_with_x_grid = P.withColumn('x_grid', get_x_grid_udf(P['x_val']))
P_with_x_and_y_grid = P_with_x_grid.withColumn('y_grid', get_y_grid_udf(P['y_val']))
P_with_grid = P_with_x_and_y_grid.withColumn('grid', get_grid_udf(P_with_x_and_y_grid['x_grid'], P_with_x_and_y_grid['y_grid']))
P_with_grid.show()

"""## Step 4: Get Count of Points in Each Grid"""

# Selct grid column
P_with_grid = P_with_grid.select('grid')

# GroupBy grid and count to get points per grid
grid_with_count = P_with_grid.groupBy('grid').agg(count('grid').alias('num_points'))

# rename grid to curr_grid to prep for join
grid_with_count = grid_with_count.withColumnRenamed("grid", "curr_grid")

grid_with_count.show()

"""## Step 5: Assign neighbors & check if valid

### Assign Neighbors

1. n_1 = curr_grid + 500 - 1

2. n_2 = curr_grid + 500

3. n_3 = curr_grid + 500 + 1

4. n_4 = curr_grid + 1

5. n_5 = curr_grid - 500 + 1

6. n_6 = curr_grid - 500

7. n_7 = curr_grid - 500 - 1

8. n_8 = curr_grid - 1

### Check if neighbor is valid

1. If x_grid = 1, then no n_1, n_8, n_7

2. If curr_grid <= 500, then no n_7, n_6, n_5

3. If curr_grid % 500 == 0, then no n_3, n_4, n_5

4. if curr_grid >= 249,951, then no n_1, n_2, n_3
"""

# Assign Neighbors & make sure valid

# Define udf to get n_1
def get_n_1(grid):
    if grid % 500 == 1:
      return -1
    elif grid >= 249951:
      return -1
    else:
      return grid + 500 - 1

get_n_1_udf = udf(get_n_1, IntegerType())

# Define udf to get n_2
def get_n_2(grid):
  if grid >= 249951:
    return -1
  else:
    return grid + 500

get_n_2_udf = udf(get_n_2, IntegerType())

# Define udf to get n_3
def get_n_3(grid):
    if grid % 500 == 0:
      return -1
    elif grid >= 249951:
      return -1
    else:
      return grid + 500 + 1

get_n_3_udf = udf(get_n_3, IntegerType())

# Define udf to get n_4
def get_n_4(grid):
    if grid % 500 == 0:
      return -1
    else:
      return grid + 1

get_n_4_udf = udf(get_n_4, IntegerType())

# Define udf to get n_5
def get_n_5(grid):
    if grid <= 500:
      return -1
    elif grid % 500 == 0:
      return -1
    else:
      return grid - 500 + 1

get_n_5_udf = udf(get_n_5, IntegerType())

# Define udf to get n_6
def get_n_6(grid):
    if grid <= 500:
      return -1
    else:
      return grid - 500

get_n_6_udf = udf(get_n_6, IntegerType())

# Define udf to get n_7
def get_n_7(grid):
    if grid % 500 == 1:
      return -1
    elif grid <= 500:
      return -1
    else:
      return grid - 500 - 1

get_n_7_udf = udf(get_n_7, IntegerType())

# Define udf to get n_8
def get_n_8(grid):
    if grid % 500 == 1:
      return -1
    else:
      return grid - 1

get_n_8_udf = udf(get_n_8, IntegerType())

# Add columns for each neighbor
P_with_n1 = P_with_grid.withColumn('n_1', get_n_1_udf(P_with_grid['grid']))
P_with_n2 = P_with_n1.withColumn('n_2', get_n_2_udf(P_with_n1['grid']))
P_with_n3 = P_with_n2.withColumn('n_3', get_n_3_udf(P_with_n2['grid']))
P_with_n4 = P_with_n3.withColumn('n_4', get_n_4_udf(P_with_n3['grid']))
P_with_n5 = P_with_n4.withColumn('n_5', get_n_5_udf(P_with_n4['grid']))
P_with_n6 = P_with_n5.withColumn('n_6', get_n_6_udf(P_with_n5['grid']))
P_with_n7 = P_with_n6.withColumn('n_7', get_n_7_udf(P_with_n6['grid']))
P_with_n8 = P_with_n7.withColumn('n_8', get_n_8_udf(P_with_n7['grid']))
grid_with_neighbors = P_with_n8.select('grid', 'n_1', 'n_2', 'n_3', 'n_4', 'n_5', 'n_6', 'n_7', 'n_8')

grid_with_neighbors.show()

"""## Step 6: Get Count of Neighbors"""

# Get grids of all points
grid_curr = P_with_grid.select('grid')

# Join grid_curr with grid_with_count based on the 'grid' column using left outer join
joined_curr = grid_curr.join(grid_with_count, grid_curr['grid'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
joined_curr_with_count = joined_curr.select(
    grid_curr['grid'],
    coalesce(grid_with_count['num_points'], lit(0)).alias('grid_count')
)

joined_curr_with_count.show()

# Get grids of all points and n1
grid_n1 = P_with_n1.select('grid', 'n_1')

# Join grid_n1 with grid_with_count based on the 'n_1' column using left outer join
joined_n1 = grid_n1.join(grid_with_count, grid_n1['n_1'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n1_with_count = joined_n1.select(
    grid_n1['grid'],
    grid_n1['n_1'].alias('n_1'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_1_count')
)

n1_with_count.show()

# Get grids of all points and n2
grid_n2 = P_with_n2.select('grid', 'n_2')

# Join grid_n2 with grid_with_count based on the 'n_2' column using left outer join
joined_n2 = grid_n2.join(grid_with_count, grid_n2['n_2'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n2_with_count = joined_n2.select(
    grid_n2['grid'],
    grid_n2['n_2'].alias('n_2'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_2_count')
)

n2_with_count.show()

# Get grids of all points and n3
grid_n3 = P_with_n3.select('grid', 'n_3')

# Join grid_n3 with grid_with_count based on the 'n_3' column using left outer join
joined_n3 = grid_n3.join(grid_with_count, grid_n3['n_3'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n3_with_count = joined_n3.select(
    grid_n3['grid'],
    grid_n3['n_3'].alias('n_3'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_3_count')
)

n3_with_count.show()

# Get grids of all points and n4
grid_n4 = P_with_n4.select('grid', 'n_4')

# Join grid_n4 with grid_with_count based on the 'n_4' column using left outer join
joined_n4 = grid_n4.join(grid_with_count, grid_n4['n_4'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n4_with_count = joined_n4.select(
    grid_n4['grid'],
    grid_n4['n_4'].alias('n_4'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_4_count')
)

n4_with_count.show()

# Get grids of all points and n5
grid_n5 = P_with_n5.select('grid', 'n_5')

# Joining grid_n5 with grid_with_count based on the 'n_5' column using left outer join
joined_n5 = grid_n5.join(grid_with_count, grid_n5['n_5'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n5_with_count = joined_n5.select(
    grid_n5['grid'],
    grid_n5['n_5'].alias('n_5'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_5_count')
)

n5_with_count.show()

# Get grids of all points and n6
grid_n6 = P_with_n6.select('grid', 'n_6')

# Joining grid_n6 with grid_with_count based on the 'n_6' column using left outer join
joined_n6 = grid_n6.join(grid_with_count, grid_n6['n_6'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n6_with_count = joined_n6.select(
    grid_n6['grid'],
    grid_n6['n_6'].alias('n_6'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_6_count')
)

n6_with_count.show()

# Get grids of all points and n7
grid_n7 = P_with_n7.select('grid', 'n_7')

# Joining grid_n7 with grid_with_count based on the 'n_7' column using left outer join
joined_n7 = grid_n7.join(grid_with_count, grid_n7['n_7'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n7_with_count = joined_n7.select(
    grid_n7['grid'],
    grid_n7['n_7'].alias('n_7'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_7_count')
)

n7_with_count.show()

# Get grids of all points and n8
grid_n8 = P_with_n8.select('grid', 'n_8')

# Joining grid_n8 with grid_with_count based on the 'n_8' column using left outer join
joined_n8 = grid_n8.join(grid_with_count, grid_n8['n_8'] == grid_with_count['curr_grid'], "left_outer")

# Replace null values in num_points with 0
n8_with_count = joined_n8.select(
    grid_n8['grid'],
    grid_n8['n_8'].alias('n_8'),
    coalesce(grid_with_count['num_points'], lit(0)).alias('n_8_count')
)

n8_with_count.show()

# Drop duplicates
joined_curr_with_count = joined_curr_with_count.dropDuplicates()
n1_with_count = n1_with_count.dropDuplicates()
n2_with_count = n2_with_count.dropDuplicates()
n3_with_count = n3_with_count.dropDuplicates()
n4_with_count = n4_with_count.dropDuplicates()
n5_with_count = n5_with_count.dropDuplicates()
n6_with_count = n6_with_count.dropDuplicates()
n7_with_count = n7_with_count.dropDuplicates()
n8_with_count = n8_with_count.dropDuplicates()

# Join all neighbors with counts based on the 'grid' column
joined_with_n1 = joined_curr_with_count.join(n1_with_count, 'grid', "outer")
joined_with_n2 = joined_with_n1.join(n2_with_count, 'grid', "outer")
joined_with_n3 = joined_with_n2.join(n3_with_count, 'grid', "outer")
joined_with_n4 = joined_with_n3.join(n4_with_count, 'grid', "outer")
joined_with_n5 = joined_with_n4.join(n5_with_count, 'grid', "outer")
joined_with_n6 = joined_with_n5.join(n6_with_count, 'grid', "outer")
joined_with_n7 = joined_with_n6.join(n7_with_count, 'grid', "outer")
joined_with_n8 = joined_with_n7.join(n8_with_count, 'grid', "outer")

joined_with_n8.show()

"""## Step 7: For each grid, calculate the density"""

from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

# Calculate average of count of all valid neighbors
def calculate_average(n1, n1_count, n2, n2_count, n3, n3_count, n4, n4_count, n5, n5_count, n6, n6_count, n7, n7_count, n8, n8_count):
    _sum = 0
    count = 0

    if n1 > 0:
        _sum += n1_count
        count += 1
    if n2 > 0:
        _sum += n2_count
        count += 1
    if n3 > 0:
        _sum += n3_count
        count += 1
    if n4 > 0:
        _sum += n4_count
        count += 1
    if n5 > 0:
        _sum += n5_count
        count += 1
    if n6 > 0:
        _sum += n6_count
        count += 1
    if n7 > 0:
        _sum += n7_count
        count += 1
    if n8 > 0:
        _sum += n8_count
        count += 1

    return _sum / count if count > 0 else None

# Register the UDF
calculate_average_udf = udf(calculate_average, DoubleType())

# Add a new column with the calculated average
joined_with_avg = joined_with_n8.withColumn('avg_count', calculate_average_udf(joined_with_n8['n_1'], joined_with_n8['n_1_count'], joined_with_n8['n_2'], joined_with_n8['n_2_count'], joined_with_n8['n_3'], joined_with_n8['n_3_count'], joined_with_n8['n_4'], joined_with_n8['n_4_count'], joined_with_n8['n_5'], joined_with_n8['n_5_count'], joined_with_n8['n_6'], joined_with_n8['n_6_count'], joined_with_n8['n_7'], joined_with_n8['n_7_count'], joined_with_n8['n_8'], joined_with_n8['n_8_count']))

joined_with_avg.show()

# Calculate relative density index
def calculate_rel_dens_index(grid_count, avg_count):
    return grid_count / avg_count

# Register the UDF
calculate_rel_dens_index_udf = udf(calculate_rel_dens_index, DoubleType())

# Add a new column with the calculated relative density
joined_with_rel_dens_index = joined_with_avg.withColumn('rel_dens_index', calculate_rel_dens_index_udf(joined_with_avg['grid_count'], joined_with_avg['avg_count']))

joined_with_rel_dens_index.show()

"""## Display the final outputs

### TOP 50 grid cells w.r.t Relative-Density Index
"""

# Rename the 'grid' column to 'curr_grid'
renamed_df = joined_with_rel_dens_index.withColumnRenamed('grid', 'curr_grid')

# Select curr_grid and rel_dens_index, order by 'rel_dens_index' in descending order, and limit to 50 rows
result = renamed_df.select('curr_grid', 'rel_dens_index').orderBy('rel_dens_index', ascending=False).limit(50)

result.show()

# Get rdi for all points
curr_rel_dens = grid_curr.join(result, grid_curr['grid'] == result['curr_grid'], "left_outer")

# Make all invalid neighbors have an rdi of 0
curr_rel_dens = curr_rel_dens.select(
    grid_curr['grid'],
    coalesce(result['rel_dens_index'], lit(0)).alias('curr_rdi')
)

curr_rel_dens.show()

# Get rdi of n1
n1_rel_dens = grid_n1.join(result, grid_n1['n_1'] == result['curr_grid'], "left_outer")
n1_rel_dens = n1_rel_dens.select(
    grid_n1['grid'],
    grid_n1['n_1'].alias('n_1'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n1_rdi')
)
n1_rel_dens.show()

# Get rdi of n2
n2_rel_dens = grid_n2.join(result, grid_n2['n_2'] == result['curr_grid'], "left_outer")
n2_rel_dens = n2_rel_dens.select(
    grid_n2['grid'],
    grid_n2['n_2'].alias('n_2'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n2_rdi')
)
n2_rel_dens.show()

# Get rdi of n3
n3_rel_dens = grid_n3.join(result, grid_n3['n_3'] == result['curr_grid'], "left_outer")
n3_rel_dens = n3_rel_dens.select(
    grid_n3['grid'],
    grid_n3['n_3'].alias('n_3'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n3_rdi')
)
n3_rel_dens.show()

# Get rdi of n4
n4_rel_dens = grid_n4.join(result, grid_n4['n_4'] == result['curr_grid'], "left_outer")
n4_rel_dens = n4_rel_dens.select(
    grid_n4['grid'],
    grid_n4['n_4'].alias('n_4'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n4_rdi')
)
n4_rel_dens.show()

# Get rdi of n5
n5_rel_dens = grid_n5.join(result, grid_n5['n_5'] == result['curr_grid'], "left_outer")
n5_rel_dens = n5_rel_dens.select(
    grid_n5['grid'],
    grid_n5['n_5'].alias('n_5'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n5_rdi')
)
n5_rel_dens.show()

# Get rdi of n6
n6_rel_dens = grid_n6.join(result, grid_n6['n_6'] == result['curr_grid'], "left_outer")
n6_rel_dens = n6_rel_dens.select(
    grid_n6['grid'],
    grid_n6['n_6'].alias('n_6'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n6_rdi')
)
n6_rel_dens.show()

# Get rdi of n7
n7_rel_dens = grid_n7.join(result, grid_n7['n_7'] == result['curr_grid'], "left_outer")
n7_rel_dens = n7_rel_dens.select(
    grid_n7['grid'],
    grid_n7['n_7'].alias('n_7'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n7_rdi')
)
n7_rel_dens.show()

# Get rdi of n8
n8_rel_dens = grid_n8.join(result, grid_n8['n_8'] == result['curr_grid'], "left_outer")
n8_rel_dens = n8_rel_dens.select(
    grid_n8['grid'],
    grid_n8['n_8'].alias('n_8'),
    coalesce(result['rel_dens_index'], lit(0)).alias('n8_rdi')
)
n8_rel_dens.show()

# Drop duplicates for joins
curr_rel_dens = curr_rel_dens.dropDuplicates()
n1_rel_dens = n1_rel_dens.dropDuplicates()
n2_rel_dens = n2_rel_dens.dropDuplicates()
n3_rel_dens = n3_rel_dens.dropDuplicates()
n4_rel_dens = n4_rel_dens.dropDuplicates()
n5_rel_dens = n5_rel_dens.dropDuplicates()
n6_rel_dens = n6_rel_dens.dropDuplicates()
n7_rel_dens = n7_rel_dens.dropDuplicates()
n8_rel_dens = n8_rel_dens.dropDuplicates()

# Joining all neighbors with rdi based on the 'grid' column
rdi_w_n1 = curr_rel_dens.join(n1_rel_dens, 'grid', "outer")
rdi_w_n2 = rdi_w_n1.join(n2_rel_dens, 'grid', "outer")
rdi_w_n3 = rdi_w_n2.join(n3_rel_dens, 'grid', "outer")
rdi_w_n4 = rdi_w_n3.join(n4_rel_dens, 'grid', "outer")
rdi_w_n5 = rdi_w_n4.join(n5_rel_dens, 'grid', "outer")
rdi_w_n6 = rdi_w_n5.join(n6_rel_dens, 'grid', "outer")
rdi_w_n7 = rdi_w_n6.join(n7_rel_dens, 'grid', "outer")
rdi_w_n8 = rdi_w_n7.join(n8_rel_dens, 'grid', "outer")

rdi_w_n8.show()

"""### Neighbors of the TOP 50 grid"""

# Select current grid and all neighbors with individual rdi's, order by 'rel_dens_index' in descending order, and limit to 50 rows
result2 = rdi_w_n8.orderBy('curr_rdi').orderBy('curr_rdi', ascending = False).limit(50)

result2.show()
### Utility Functions
import pandas as pd
import sqlite3
from sqlite3 import Error

def create_connection(db_file, delete_db=False):
    import os
    if delete_db and os.path.exists(db_file):
        os.remove(db_file)

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = 1")
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql, drop_table_name=None):
    
    if drop_table_name: # You can optionally pass drop_table_name to drop the table. 
        try:
            c = conn.cursor()
            c.execute("""DROP TABLE IF EXISTS %s""" % (drop_table_name))
        except Error as e:
            print(e)
    
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
        
def execute_sql_statement(sql_statement, conn):
    cur = conn.cursor()
    cur.execute(sql_statement)

    rows = cur.fetchall()

    return rows

def step1_create_region_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None
  
  regions=set()
  with open(data_filename, "r") as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts)>=5:
        r= parts[4]
        regions.add(r)
  
  s_region = sorted(list(regions))
  conn= create_connection(normalized_database_filename)

  region_sql= """ CREATE TABLE IF NOT EXISTS Region (
        RegionID INTEGER NOT NULL PRIMARY KEY,
        Region TEXT NOT NULL
    );"""

  create_table(conn, region_sql, "Region")

  values=[(region,) for region in s_region]

  with conn:
    cur=conn.cursor()
    cur.executemany("INSERT INTO Region (Region) VALUES (?)", values)
  
  conn.close()


def step2_create_region_to_regionid_dictionary(normalized_database_filename):
  conn= create_connection(normalized_database_filename)
  sql = "Select Region, RegionID from Region"
  values = execute_sql_statement(sql, conn)
  region_dict = {v[0]: v[1] for v in values}
  conn.close()

  return region_dict
    
    
# WRITE YOUR CODE HERE


def step3_create_country_table(data_filename, normalized_database_filename):
  r_dict = step2_create_region_to_regionid_dictionary(normalized_database_filename)
  cnt_set = set()
  with open(data_filename, "r") as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts) >=5:
        country=parts[3]
        region=parts[4]
        cnt_set.add((country, region))

  sort_cnt = sorted(list(cnt_set), key=lambda x: x[0])

  conn=create_connection(normalized_database_filename)

  sql="""CREATE TABLE IF NOT EXISTS Country(
    CountryID INTEGER NOT NULL PRIMARY KEY,
        Country TEXT NOT NULL,
        RegionID INTEGER NOT NULL,
        FOREIGN KEY (RegionID) REFERENCES Region(RegionID)
  )"""

  create_table(conn, sql, 'Country')
  values=[(country, r_dict[region]) for country, region in sort_cnt]

  with conn:
    cur= conn.cursor()
    cur.executemany("INSERT INTO Country (Country, RegionID) VALUES (?, ?)", values)

  conn.close()


def step4_create_country_to_countryid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)
  sql = "Select Country, CountryID FROM Country"
  rows= execute_sql_statement(sql, conn)

  country_dict = {row[0]: row[1] for row in rows}
  conn.close()

  return country_dict
    
    
# WRITE YOUR CODE HERE
        
        
def step5_create_customer_table(data_filename, normalized_database_filename):
  country_dict= step4_create_country_to_countryid_dictionary(normalized_database_filename)

  customers=set()
  with open(data_filename, "r") as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts)>=5:
        name = parts[0]
        address = parts[1]
        city = parts[2]
        country=parts[3]

        name_part=name.split()
        f_name=name_part[0]
        if len(name_part)>=3:
          l_name = " ".join(name_part[1:])
        else:
          l_name = name_part[1]

        customers.add((f_name, l_name, address, city, country))
  sort_cust = sorted(list(customers), key= lambda x:x[0]+' '+ x[1])
  conn=create_connection(normalized_database_filename)

  sql= """CREATE TABLE IF NOT EXISTS Customer (
        CustomerID INTEGER NOT NULL PRIMARY KEY,
        FirstName TEXT NOT NULL,
        LastName TEXT NOT NULL,
        Address TEXT NOT NULL,
        City TEXT NOT NULL,
        CountryID INTEGER NOT NULL,
        FOREIGN KEY (CountryID) REFERENCES Country(CountryID)
    );"""

  create_table(conn, sql, "Customer")

  values=[(f, l, a, city, country_dict[country]) for f, l, a, city, country in sort_cust]
  with conn:
    cur=conn.cursor()
    cur.executemany("INSERT INTO Customer (FirstName, LastName, Address, City, CountryID) VALUES (?, ?, ?, ?, ?)", values)
  conn.close()

# WRITE YOUR CODE HERE


def step6_create_customer_to_customerid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)

  sql = "SELECT FirstName, LastName, CustomerID FROM Customer"
  rows = execute_sql_statement(sql, conn)

  customer_dict= {row[0]+ " "+row[1]:row[2] for row in rows}

  conn.close()

  return customer_dict
    
    
# WRITE YOUR CODE HERE
        
def step7_create_productcategory_table(data_filename, normalized_database_filename):
  catg=set()
  with open(data_filename, 'r') as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts) >= 11:
        prod_cat=parts[6].split(";")
        prod_desc=parts[7].split(";")

        for cat, desc in zip(prod_cat, prod_desc):
          catg.add((cat,desc))
  sort_cat= sorted(list(catg), key=lambda x:x[0])

  conn=create_connection(normalized_database_filename)
  sql = """
    CREATE TABLE IF NOT EXISTS ProductCategory (
        ProductCategoryID INTEGER NOT NULL PRIMARY KEY,
        ProductCategory TEXT NOT NULL,
        ProductCategoryDescription TEXT NOT NULL
    );
    """
  
  create_table(conn, sql, "ProductCategory")
  values = [(cat, desc) for cat, desc in sort_cat]

  with conn:
    cur=conn.cursor()
    cur.executemany("INSERT INTO ProductCategory (ProductCategory, ProductCategoryDescription) VALUES (?, ?)", values)
  conn.close()


def step8_create_productcategory_to_productcategoryid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)

  sql = "SELECT ProductCategory, ProductCategoryID FROM ProductCategory"
  rows = execute_sql_statement(sql, conn)

  product_dict= {row[0]:row[1] for row in rows}

  conn.close()

  return product_dict
    
    
# WRITE YOUR CODE HERE
        

def step9_create_product_table(data_filename, normalized_database_filename):
  product_dict=step8_create_productcategory_to_productcategoryid_dictionary(normalized_database_filename)

  products=set()
  with open(data_filename, "r") as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts)>=11:
        p_name=parts[5].split(';')
        p_cat=parts[6].split(';')
        p_prices=parts[8].split(';')

        for name, car, price in zip(p_name, p_cat, p_prices):
          products.add((name, float(price), car))

  sorted_prod = sorted(list(products), key=lambda x:x[0])

  conn=create_connection(normalized_database_filename)
  sql = """
    CREATE TABLE IF NOT EXISTS Product (
        ProductID INTEGER NOT NULL PRIMARY KEY,
        ProductName TEXT NOT NULL,
        ProductUnitPrice REAL NOT NULL,
        ProductCategoryID INTEGER NOT NULL,
        FOREIGN KEY (ProductCategoryID) REFERENCES ProductCategory(ProductCategoryID)
    );
    """
  
  create_table(conn, sql, "Product")
  values = [(name, price, product_dict[cat]) for name, price, cat in sorted_prod]

  with conn:
    cur=conn.cursor()
    cur.executemany("INSERT INTO Product (ProductName, ProductUnitPrice, ProductCategoryID) VALUES (?, ?, ?)", values)
  conn.close()

def step10_create_product_to_productid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)

  sql = "SELECT ProductName, ProductID FROM Product"
  rows = execute_sql_statement(sql, conn)

  product_dict= {row[0]:row[1] for row in rows}

  conn.close()

  return product_dict
    
# WRITE YOUR CODE HERE
        

def step11_create_orderdetail_table(data_filename, normalized_database_filename):
  cust_dict=step6_create_customer_to_customerid_dictionary(normalized_database_filename)
  prod_dict=step10_create_product_to_productid_dictionary(normalized_database_filename)

  orders=[]
  with open(data_filename, "r") as f:
    next(f)
    for line in f:
      parts=line.strip().split("\t")
      if len(parts)>=11:
        name=parts[0]
        p_name=parts[5].split(';')
        qt=parts[9].split(';')
        o_date=parts[10].split(';')

        for p,q,d in zip(p_name, qt, o_date):
          cust_id=cust_dict[name]
          prod_id=prod_dict[p]
          date_str=str(d)
          new_date= f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
          orders.append((cust_id, prod_id, new_date,int(q)))
  
  conn=create_connection(normalized_database_filename)
  sql = """
    CREATE TABLE IF NOT EXISTS OrderDetail (
        OrderID INTEGER NOT NULL PRIMARY KEY,
        CustomerID INTEGER NOT NULL,
        ProductID INTEGER NOT NULL,
        OrderDate INTEGER NOT NULL,
        QuantityOrdered INTEGER NOT NULL,
        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
        FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    );
    """
  
  create_table(conn, sql, "OrderDetail")
  with conn:
    cur=conn.cursor()
    cur.executemany("INSERT INTO OrderDetail (CustomerID, ProductID, OrderDate, QuantityOrdered) VALUES (?, ?, ?, ?)", orders)
  conn.close()



def ex1(conn, CustomerName):
    
    # Simply, you are fetching all the rows for a given CustomerName. 
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # ProductName
    # OrderDate
    # ProductUnitPrice
    # QuantityOrdered
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- round to two decimal places
    # HINT: USE customer_to_customerid_dict to map customer name to customer id and then use where clause with CustomerID
  cust_dict= step6_create_customer_to_customerid_dictionary('normalized.db')
  cust_id=cust_dict[CustomerName]
  sql_statement = f"""
    SELECT c.FirstName || ' ' || c.LastName AS Name,
    p.ProductName, od.OrderDate, p.ProductUnitPrice, od.QuantityOrdered,
    Round((p.ProductUnitPrice * od.QuantityOrdered),2)  as Total
    From OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Product p ON od.ProductID = p.ProductID
    WHERE c.CustomerID = {cust_id}
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex2(conn, CustomerName):
  cust_dict= step6_create_customer_to_customerid_dictionary('normalized.db')
  cust_id=cust_dict[CustomerName]
    # Simply, you are summing the total for a given CustomerName. 
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # HINT: USE customer_to_customerid_dict to map customer name to customer id and then use where clause with CustomerID
    
  sql_statement = f"""
    SELECT c.FirstName || ' ' || c.LastName AS Name,
    ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered), 2) AS Total
    From OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Product p ON od.ProductID = p.ProductID
    WHERE c.CustomerID = {cust_id}
    GROUP BY c.FirstName, c.LastName
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex3(conn):
    
    # Simply, find the total for all the customers
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # ORDER BY Total Descending 
    
  sql_statement = """
    SELECT c.FirstName || ' ' || c.LastName AS Name,
    ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered), 2) AS Total
    From OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Product p ON od.ProductID = p.ProductID
    GROUP BY c.CustomerID, c.FirstName, c.LastName
    ORDER BY Total DESC
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex4(conn):
    
    # Simply, find the total for all the region
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer, Product, Country, and 
    # Region tables.
    # Pull out the following columns. 
    # Region
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # ORDER BY Total Descending 
    
  sql_statement = """
    SELECT r.Region,
    ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered), 2) AS Total
    FROM OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Product p ON od.ProductID = p.ProductID
    JOIN Country cu on c.CountryID = cu.CountryID
    JOIN Region r ON cu.RegionID = r.RegionID
    GROUP BY r.Region
    ORDER BY Total DESC
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex5(conn):
    
    # Simply, find the total for all the countries
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer, Product, and Country table.
    # Pull out the following columns. 
    # Country
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round
    # ORDER BY Total Descending 

  sql_statement = """
    SELECT cu.Country,
    ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered)) AS Total
    FROM OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Product p ON od.ProductID = p.ProductID
    JOIN Country cu on c.CountryID = cu.CountryID
    GROUP BY cu.Country
    ORDER BY Total DESC
    """

# WRITE YOUR CODE HERE
  return sql_statement


def ex6(conn):
    
    # Rank the countries within a region based on order total
    # Output Columns: Region, Country, CountryTotal, TotalRank
    # Hint: Round the the total
    # Hint: Sort ASC by Region

  sql_statement = """
  SELECT r.Region, cu.Country, ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered) ) AS CountryTotal,
  RANK() OVER (PARTITION BY r.Region ORDER BY SUM(p.ProductUnitPrice * od.QuantityOrdered) DESC) AS TotalRank
  FROM OrderDetail od
  JOIN Customer c ON od.CustomerID = c.CustomerID
  JOIN Product p ON od.ProductID = p.ProductID
  JOIN Country cu on c.CountryID = cu.CountryID
  JOIN Region r ON cu.RegionID = r.RegionID
  GROUP BY r.Region, cu.Country
  ORDER BY r.Region ASC
  """

# WRITE YOUR CODE HERE
  df = pd.read_sql_query(sql_statement, conn)
  return sql_statement



def ex7(conn):
    
    # Rank the countries within a region based on order total, BUT only select the TOP country, meaning rank = 1!
    # Output Columns: Region, Country, Total, TotalRank
    # Hint: Round the the total
    # Hint: Sort ASC by Region
    # HINT: Use "WITH"

  sql_statement = """ WITH RankedCountries AS (
  SELECT r.Region, cu.Country, ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered)) AS CountryTotal,
  RANK() OVER (PARTITION BY r.Region ORDER BY SUM(p.ProductUnitPrice * od.QuantityOrdered) DESC) AS CountryRegionalRank
  FROM OrderDetail od
  JOIN Customer c ON od.CustomerID = c.CustomerID
  JOIN Product p ON od.ProductID = p.ProductID
  JOIN Country cu on c.CountryID = cu.CountryID
  JOIN Region r ON cu.RegionID = r.RegionID
  GROUP BY r.Region, cu.Country 
  )

  SELECT Region, Country, CountryTotal, CountryRegionalRank
  FROM RankedCountries
  WHERE CountryRegionalRank = 1
  ORDER BY Region ASC
  """
# WRITE YOUR CODE HERE
  return sql_statement

def ex8(conn):
    
    # Sum customer sales by Quarter and year
    # Output Columns: Quarter,Year,CustomerID,Total
    # HINT: Use "WITH"
    # Hint: Round the the total
    # HINT: YOU MUST CAST YEAR TO TYPE INTEGER!!!!

  sql_statement = """
    WITH CustomerSales AS (
      SELECT
      CASE
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
      ELSE 'Q4'
      END AS Quarter,
      CAST(SUBSTR(od.OrderDate,1,4) AS INTEGER) AS Year,
      od.CustomerID,
      ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered)) AS Total
    FROM OrderDetail od
    JOIN Product p ON od.ProductID = p.ProductID
    GROUP BY Quarter, Year, od.CustomerID)
    SELECT Quarter, Year, CustomerID, Total
    FROM CustomerSales
    ORDER BY Year  
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex9(conn):
    
    # Rank the customer sales by Quarter and year, but only select the top 5 customers!
    # Output Columns: Quarter, Year, CustomerID, Total
    # HINT: Use "WITH"
    # Hint: Round the the total
    # HINT: YOU MUST CAST YEAR TO TYPE INTEGER!!!!
    # HINT: You can have multiple CTE tables;
    # WITH table1 AS (), table2 AS ()

  sql_statement = """
  WITH CustomerSales AS (
      SELECT
      CASE
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
      WHEN CAST(SUBSTR(od.OrderDate,6,2) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
      ELSE 'Q4'
      END AS Quarter,
      CAST(SUBSTR(od.OrderDate,1,4) AS INTEGER) AS Year,
      od.CustomerID,
      ROUND(SUM(p.ProductUnitPrice * od.QuantityOrdered)) AS Total
    FROM OrderDetail od
    JOIN Product p ON od.ProductID = p.ProductID
    GROUP BY Quarter, Year, od.CustomerID),
    RankedSales AS(
      SELECT Quarter, Year, CustomerID, Total,
      RANK() OVER (PARTITION BY Quarter, Year ORDER BY Total DESC) AS CustomerRank
      FROM CustomerSales
    )
    SELECT Quarter,Year,CustomerID,Total,CustomerRank
    FROM RankedSales
    WHERE CustomerRank <=5 
    ORDER BY Year
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex10(conn):
    
    # Rank the monthy sales
    # Output Columns: Quarter, Year, CustomerID, Total
    # HINT: Use "WITH"
    # Hint: Round the the total

  sql_statement = """
  WITH MonthlySales AS (
    SELECT 
    CASE SUBSTR(od.OrderDate, 6,2)
    WHEN '01' THEN 'January'
    WHEN '02' THEN 'February'
    WHEN '03' THEN 'March'
    WHEN '04' THEN 'April'
    WHEN '05' THEN 'May'
    WHEN '06' THEN 'June'
    WHEN '07' THEN 'July'
    WHEN '08' THEN 'August'
    WHEN '09' THEN 'September'
    WHEN '10' THEN 'October'
    WHEN '11' THEN 'November'
    WHEN '12' THEN 'December'
    END AS Month,


    SUM(ROUND(p.ProductUnitPrice * od.QuantityOrdered)) AS Total
    FROM Product p
    JOIN OrderDetail od ON od.ProductID = p.ProductID
    GROUP BY Month
  )
  SELECT Month, Round(Total) AS Total, RANK() OVER (ORDER BY Total DESC) AS TotalRank
  From MonthlySales
    """

# WRITE YOUR CODE HERE
  return sql_statement

def ex11(conn):
    
    # Find the MaxDaysWithoutOrder for each customer 
    # Output Columns: 
    # CustomerID,
    # FirstName,
    # LastName,
    # Country,
    # OrderDate, 
    # PreviousOrderDate,
    # MaxDaysWithoutOrder
    # order by MaxDaysWithoutOrder desc
    # HINT: Use "WITH"; I created two CTE tables
    # HINT: Use Lag
  sql_statement = """
  WITH CustomerOrders AS(
    SELECT
    c.CustomerID, c.FirstName, c.LastName, cu.Country, od.OrderDate,
    LAG(od.OrderDate) OVER (PARTITION BY c.CustomerID ORDER BY od.OrderDate) AS PreviousOrderDate
    FROM OrderDetail od
    JOIN Customer c ON od.CustomerID=c.CustomerID
    JOIN Country cu ON c.CountryID=cu.CountryID
  ),
  DaysBetweenOrders AS(
    SELECT CustomerID, FirstName, LastName, Country, OrderDate, PreviousOrderDate,
    JULIANDAY(OrderDate)-JULIANDAY(PreviousOrderDate) AS DaysWithoutOrder
    FROM CustomerOrders
    WHERE PreviousOrderDate IS NOT NULL
  ),
  MaxDays AS(
    SELECT CustomerID,MAX(DaysWithoutOrder) AS MaxDaysWithoutOrder FROM DaysBetweenOrders GROUP BY CustomerID
  )
  SELECT d.CustomerID,d.FirstName,d.LastName,d.Country,d.OrderDate, d.PreviousOrderDate, m.MaxDaysWithoutOrder
  FROM DaysBetweenOrders d
  JOIN MaxDays m ON d.CustomerID=m.CustomerID AND d.DaysWithoutOrder=m.MaxDaysWithoutOrder
  WHERE d.OrderDate =(
    SELECT MIN(db.OrderDate)
    FROM DaysBetweenOrders db
    JOIN MaxDays md on db.CustomerID = md.CustomerID and db.DaysWithoutOrder = md.MaxDaysWithoutOrder
    WHERE db.CustomerID=d.CustomerID
  )
  ORDER BY m.MaxDaysWithoutOrder DESC, d.CustomerID DESC
    """
# WRITE YOUR CODE HERE
  return sql_statement


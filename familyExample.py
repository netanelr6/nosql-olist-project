
#1.ducument DB
{
  "_id": "e481f51cbdc54678b7cc49136f2d6af7",
  "order_status": "delivered",
  "order_purchase_timestamp": "2017-10-02T10:56:33Z",
  "order_approved_at": "2017-10-02T11:07:15Z",
  "order_delivered_customer_date": "2017-10-10T21:25:13Z",
  "order_estimated_delivery_date": "2017-10-18T00:00:00Z",
  
  "customer": {
    "customer_id": "9ef432eb6251297304e76186b10a928d",
    "customer_unique_id": "7c396fd4830fd04220f754e42b4e5bff",
    "customer_zip_code_prefix": "03149",
    "customer_city": "sao paulo",
    "customer_state": "SP"
  },
  
  "payments": [
    {
      "payment_sequential": 1,
      "payment_type": "credit_card",
      "payment_installments": 1,
      "payment_value": 18.12
    },
    {
      "payment_sequential": 2,
      "payment_type": "voucher",
      "payment_installments": 1,
      "payment_value": 2.00
    },
    {
      "payment_sequential": 3,
      "payment_type": "voucher",
      "payment_installments": 1,
      "payment_value": 18.59
    }
  ],
  
  "items": [
    {
      "order_item_id": 1,
      "product_id": "87285b34884572647811a353c7ac498a",
      "seller_id": "3504c0cb71d7fa48d967e0e4c94d59d9",
      "shipping_limit_date": "2017-10-06T11:07:15Z",
      "price": 29.99,
      "freight_value": 8.72
    }
  ]
}


#------------------------------------------------------------
#2. Column DB


# Olist Column-Family Store representation
olist_column_store = {
    
    # Row Key: customer_unique_id (Full 32-char string)
    "8d50f5eadf50201ccdcedfb9e2ac8455": {
        
        # Column Family 1: Profile
        "Profile:City": "sao paulo",
        "Profile:State": "SP",
        
        # Column Family 2: Orders (Dynamic columns - No schema limit!)
        # Key is "Orders:<order_id>", Value is total payment/freight
        "Orders:e481f51cbdc54678b7cc49136f2d6af7": "105.12", 
        "Orders:53cdb2fc8bc7dce0b6741e2150273451": "29.99",
        "Orders:47770eb9100c2d0c44946d9cf07ec65d": "50.00" 
    },
    
    # Row Key: customer_unique_id
    "36edbb3fb164b1f16485364b6fa1dae1": {
        
        "Profile:City": "rio de janeiro",
        "Profile:State": "RJ",
        
        # This customer has only 1 order. No NULLs stored.
        "Orders:b2b6027bc5c5109e529d4dc6358b12c3": "8.72" 
    }
}

# --- Querying the data ---
# Fetching all customer data (Profile + All Orders) in O(1) time.
customer_data = olist_column_store["8d50f5eadf50201ccdcedfb9e2ac8455"]



#------------------------------------------------


#3.  
"""

# Cache initialization (Background process to sync DB with Cache)
SET "product:87285b34884572647811a353c7ac498a" '{"category":"utilidades_domesticas", "weight_g":238, "price": 29.99, "photos_qty":1}'

# Real-time retrieval (Triggers when a customer clicks a product)
GET "product:87285b34884572647811a353c7ac498a"

# Result (Instant delivery of data to the web server)
> '{"category":"utilidades_domesticas", "weight_g":238, "price": 29.99, "photos_qty":1}'

"""

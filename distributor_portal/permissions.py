import frappe

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════

ALLOWED_ITEM_GROUPS = [
    "Manufactured Products (منتجات التصنيع)",
    "Purchased Products (منتجات مشتراه)",
]

HIDDEN_PRICE_LISTS = [
    "Standard Buying",
]

# Warehouses distributors can see
ALLOWED_WAREHOUSES = [
    "مخزن طلبيات الموزعين والعملاء - C",
]

# ═══════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════

def is_distributor(user=None):
    if not user:
        user = frappe.session.user
    if user == "Administrator":
        return False
    return "Distributor" in frappe.get_roles(user)

def get_linked_customer(user=None):
    """Get customer linked to this user via User Permission."""
    if not user:
        user = frappe.session.user
    
    # Method 1: Via User Permission (most reliable for your setup)
    user_perm = frappe.db.get_value("User Permission",
        {"user": user, "allow": "Customer", "applicable_for": "Sales Invoice"},
        "for_value"
    )
    if user_perm:
        return user_perm
    
    # Method 2: Any User Permission for Customer (broader search)
    user_perm = frappe.db.get_value("User Permission",
        {"user": user, "allow": "Customer"},
        "for_value"
    )
    if user_perm:
        return user_perm
    
    # Method 3: Via Contact -> Customer link
    contact = frappe.db.get_value("Contact", {"user": user}, "name")
    if contact:
        links = frappe.get_all("Dynamic Link",
            filters={
                "parenttype": "Contact",
                "parent": contact,
                "link_doctype": "Customer"
            },
            fields=["link_name"],
            limit=1
        )
        if links:
            return links[0].link_name
    
    return None

# ═══════════════════════════════════════════════
# ITEM
# ═══════════════════════════════════════════════

def get_item_permission(user):
    if not is_distributor(user):
        return ""
    
    groups = "', '".join(ALLOWED_ITEM_GROUPS)
    return f"""(`tabItem`.`item_group` IN ('{groups}'))"""

def has_item_permission(doc, user=None, permission_type=None):
    if not is_distributor(user):
        return True
    return doc.item_group in ALLOWED_ITEM_GROUPS

# ═══════════════════════════════════════════════
# ITEM PRICE
# ═══════════════════════════════════════════════

def get_item_price_permission(user):
    if not is_distributor(user):
        return ""
    
    lists = "', '".join(HIDDEN_PRICE_LISTS)
    return f"""(`tabItem Price`.`price_list` NOT IN ('{lists}'))"""

def has_item_price_permission(doc, user=None, permission_type=None):
    if not is_distributor(user):
        return True
    return doc.price_list not in HIDDEN_PRICE_LISTS

# ═══════════════════════════════════════════════
# WAREHOUSE
# ═══════════════════════════════════════════════

def get_warehouse_permission(user):
    if not is_distributor(user):
        return ""
    
    warehouses = "', '".join(ALLOWED_WAREHOUSES)
    return f"""(`tabWarehouse`.`name` IN ('{warehouses}'))"""

def has_warehouse_permission(doc, user=None, permission_type=None):
    if not is_distributor(user):
        return True
    return doc.name in ALLOWED_WAREHOUSES

# ═══════════════════════════════════════════════
# SALES ORDER
# ═══════════════════════════════════════════════

def get_sales_order_permission(user):
    if not is_distributor(user):
        return ""
    
    customer = get_linked_customer(user)
    if not customer:
        return "(1=0)"
    
    return f"""(`tabSales Order`.`customer` = '{customer}')"""

# ═══════════════════════════════════════════════
# SALES INVOICE
# ═══════════════════════════════════════════════

def get_sales_invoice_permission(user):
    if not is_distributor(user):
        return ""
    
    customer = get_linked_customer(user)
    if not customer:
        return "(1=0)"
    
    return f"""(`tabSales Invoice`.`customer` = '{customer}' 
        AND `tabSales Invoice`.`status` != 'Cancelled')"""

def has_sales_invoice_permission(doc, user=None, permission_type=None):
    if not is_distributor(user):
        return True
    if doc.status == "Cancelled":
        return False
    return True

import asyncio
from mcp.server.fastmcp import FastMCP
from transactional_db import CUSTOMERS_TABLE, ORDERS_TABLE, PRODUCTS_TABLE

mcp = FastMCP("ecommerce_tools")

# ...

@mcp.tool()
async def get_order_details(order_id: str) -> str:
    """Get details about a specific order."""
    await asyncio.sleep(1)
    order = ORDERS_TABLE.get(order_id)
    if not order:
        return f"No order found with ID {order_id}."

    items = [
        PRODUCTS_TABLE[sku]["name"]
        for sku in order["items"]
        if sku in PRODUCTS_TABLE
    ]
    total_value = order.get("total", 0)
    try:
        total_amount = float(total_value)
    except (TypeError, ValueError):
        total_amount = 0.0

    return (
        f"Order ID: {order_id}\n"
        f"Customer ID: {order['customer_id']}\n"
        f"Date: {order['date']}\n"
        f"Status: {order['status']}\n"
        f"Total: ${total_amount:.2f}\n"
        f"Items: {', '.join(items)}"
    )

@mcp.tool()
async def check_inventory(product_name: str) -> str:
    """Search inventory for a product by product name."""
    await asyncio.sleep(1)
    matches = []
    for sku, product in PRODUCTS_TABLE.items():
        if product_name.lower() in product["name"].lower():
            matches.append(
                f"{product['name']} (SKU: {sku}) — Stock: {product['stock']}"
            )
    return "\n".join(matches) if matches else "No matching products found."

@mcp.tool()
async def get_customer_ids_by_name(customer_name: str) -> list[str]:
    """Get customer IDs by using a customer's full name"""
    await asyncio.sleep(1)
    return [
        cust_id
        for cust_id, info in CUSTOMERS_TABLE.items()
        if info.get("name") == customer_name
    ]

@mcp.tool()
async def get_orders_by_customer_id(
    customer_id: str,
) -> str:
    """Get orders by customer ID"""
    await asyncio.sleep(1)
    matching_orders = {
        order_id: order
        for order_id, order in ORDERS_TABLE.items()
        if order.get("customer_id") == customer_id
    }

    if not matching_orders:
        return f"No orders found for customer ID {customer_id}."

    lines = []
    for order_id, order in matching_orders.items():
        items = [
            PRODUCTS_TABLE[sku]["name"]
            for sku in order.get("items", [])
            if sku in PRODUCTS_TABLE
        ]
        total_value = order.get("total", 0)
        try:
            total_amount = float(total_value)
        except (TypeError, ValueError):
            total_amount = 0.0

        lines.append(
            f"Order ID: {order_id} | Date: {order['date']} | Status: {order['status']} | Total: ${total_amount:.2f} | Items: {', '.join(items)}"
        )

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run(transport="stdio")
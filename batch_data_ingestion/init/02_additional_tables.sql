-- Create order_items table for order line items
CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create inventory_locations table
CREATE TABLE inventory_locations (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_code VARCHAR(10),
    city VARCHAR(50),
    country VARCHAR(50),
    capacity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create product_inventory table to track product stock at different locations
CREATE TABLE product_inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    location_id INT,
    quantity INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id)
);

-- Insert sample data
INSERT INTO inventory_locations (warehouse_code, city, country, capacity) VALUES
    ('WH-001', 'San Francisco', 'USA', 10000),
    ('WH-002', 'New York', 'USA', 15000),
    ('WH-003', 'London', 'UK', 12000);

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 999.99),
    (2, 2, 1, 699.99),
    (2, 3, 1, 199.99),
    (3, 3, 1, 199.99);

-- Insert sample inventory data
INSERT INTO product_inventory (product_id, location_id, quantity) VALUES
    (1, 1, 20),
    (1, 2, 30),
    (2, 1, 40),
    (2, 3, 60),
    (3, 2, 25),
    (3, 3, 50);

-- Staff Service Database Schema
-- This script creates the necessary tables for the staff management service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Staff users table (for staff authentication and management)
CREATE TABLE staff_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'manager', 'support', 'content')),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customer users table (synced from auth service or managed here)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id VARCHAR(255) UNIQUE, -- Reference to auth service user ID
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'Standard',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    total_spent DECIMAL(10,2) DEFAULT 0.0,
    api_calls INTEGER DEFAULT 0,
    last_active TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Support tickets table
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in-progress', 'waiting-customer', 'resolved', 'closed')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    category VARCHAR(50) NOT NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES staff_users(id) ON DELETE SET NULL,
    response_time_hours DECIMAL(5,2),
    message_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ticket messages table (for ticket conversations)
CREATE TABLE ticket_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('customer', 'staff')),
    sender_id UUID NOT NULL, -- References either customers.id or staff_users.id
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false, -- Internal staff notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System audit log for staff actions
CREATE TABLE staff_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID REFERENCES staff_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customer sessions/tracking
CREATE TABLE customer_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_staff_users_username ON staff_users(username);
CREATE INDEX idx_staff_users_email ON staff_users(email);
CREATE INDEX idx_staff_users_role ON staff_users(role);
CREATE INDEX idx_staff_users_active ON staff_users(is_active);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_plan ON customers(plan);
CREATE INDEX idx_customers_auth_user_id ON customers(auth_user_id);

CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_tickets_assigned_to ON support_tickets(assigned_to);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_category ON support_tickets(category);
CREATE INDEX idx_support_tickets_created_at ON support_tickets(created_at);
CREATE INDEX idx_support_tickets_ticket_number ON support_tickets(ticket_number);

CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX idx_ticket_messages_sender_type ON ticket_messages(sender_type);
CREATE INDEX idx_ticket_messages_created_at ON ticket_messages(created_at);

CREATE INDEX idx_staff_audit_log_staff_id ON staff_audit_log(staff_id);
CREATE INDEX idx_staff_audit_log_action ON staff_audit_log(action);
CREATE INDEX idx_staff_audit_log_created_at ON staff_audit_log(created_at);

CREATE INDEX idx_customer_sessions_customer_id ON customer_sessions(customer_id);
CREATE INDEX idx_customer_sessions_session_token ON customer_sessions(session_token);
CREATE INDEX idx_customer_sessions_is_active ON customer_sessions(is_active);
CREATE INDEX idx_customer_sessions_expires_at ON customer_sessions(expires_at);

-- Update timestamps function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updating timestamps
CREATE TRIGGER update_staff_users_updated_at BEFORE UPDATE ON staff_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to mcp_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;

-- Create default admin staff user (password: admin123 - change in production)
INSERT INTO staff_users (username, email, full_name, password_hash, role, department) 
VALUES (
    'admin',
    'admin@system.local',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', -- bcrypt hash of 'admin123'
    'admin',
    'System'
);

-- Create sample support staff users
INSERT INTO staff_users (username, email, full_name, password_hash, role, department) 
VALUES 
    ('sarah.wilson', 'sarah.wilson@staff.com', 'Sarah Wilson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', 'support', 'Customer Support'),
    ('mike.support', 'mike.support@staff.com', 'Mike Johnson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', 'support', 'Customer Support'),
    ('alex.chen', 'alex.chen@staff.com', 'Alex Chen', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', 'manager', 'Operations');

-- Create sample customers
INSERT INTO customers (username, email, full_name, plan, status, total_spent, api_calls) 
VALUES 
    ('john.doe', 'john.doe@example.com', 'John Doe', 'Pro', 'active', 237.0, 15847),
    ('jane.smith', 'jane.smith@company.com', 'Jane Smith', 'Enterprise', 'active', 1200.0, 45231),
    ('mike.johnson', 'mike@startup.io', 'Mike Johnson', 'Standard', 'inactive', 87.0, 3421);

-- Create sample support tickets
INSERT INTO support_tickets (ticket_number, title, description, status, priority, category, customer_id, assigned_to, response_time_hours, message_count)
VALUES 
    ('T-2024-001', 'API Rate Limiting Issues', 'Experiencing unexpected rate limiting on API calls despite being under the limit.', 'in-progress', 'high', 'API', 
     (SELECT id FROM customers WHERE username = 'john.doe'), 
     (SELECT id FROM staff_users WHERE username = 'sarah.wilson'), 2.5, 4),
    ('T-2024-002', 'Billing Discrepancy', 'Charged twice for the same subscription period.', 'waiting-customer', 'medium', 'Billing', 
     (SELECT id FROM customers WHERE username = 'jane.smith'), 
     (SELECT id FROM staff_users WHERE username = 'mike.support'), 4.2, 6),
    ('T-2024-003', 'Code Editor Performance Issues', 'Code editor becomes slow with large files over 1000 lines.', 'open', 'medium', 'Performance', 
     (SELECT id FROM customers WHERE username = 'mike.johnson'), NULL, NULL, 1);

-- Create sample ticket messages
INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, message, is_internal)
VALUES 
    ((SELECT id FROM support_tickets WHERE ticket_number = 'T-2024-001'), 'customer', 
     (SELECT id FROM customers WHERE username = 'john.doe'), 
     'I''m experiencing unexpected rate limiting on my API calls. My account shows I''m well under the monthly limit, but I''m getting 429 errors.', false),
    ((SELECT id FROM support_tickets WHERE ticket_number = 'T-2024-001'), 'staff', 
     (SELECT id FROM staff_users WHERE username = 'sarah.wilson'), 
     'Thank you for reporting this. I''m investigating the rate limiting issue and will get back to you shortly.', false),
    ((SELECT id FROM support_tickets WHERE ticket_number = 'T-2024-001'), 'staff', 
     (SELECT id FROM staff_users WHERE username = 'sarah.wilson'), 
     'Internal note: The rate limiting configuration appears to be incorrect. Need to check the API gateway settings.', true);

-- Update sequences for ticket numbers
CREATE SEQUENCE ticket_number_seq START WITH 1000;

-- Function to generate ticket numbers
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS VARCHAR AS $$
DECLARE
    year VARCHAR(4);
    sequence_num INTEGER;
BEGIN
    year := EXTRACT(YEAR FROM CURRENT_DATE)::VARCHAR;
    EXECUTE format('SELECT nextval(''ticket_number_seq'')') INTO sequence_num;
    RETURN 'T-' || year || '-' || LPAD(sequence_num::VARCHAR, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Set the sequence to the next available number
SELECT setval('ticket_number_seq', 4); -- We already have 3 tickets
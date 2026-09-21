/**
 * server.js - Express server cho NAC CRM
 * 
 * Bao gồm:
 * - JWT authentication middleware
 * - Tất cả API endpoints (auth, users, customers, records, transactions, dashboard, reports, notifications, data)
 * - Seed data khi khởi động lần đầu
 * - Kiểm tra deadline hồ sơ sắp hết hạn / quá hạn
 * - Phân trang cho tất cả danh sách
 */

const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const path = require('path');
const { initDatabase, generateCustomerCode, generateRecordCode, generateTransactionCode } = require('./database');

const app = express();
const PORT = 3000;
const JWT_SECRET = 'nac-crm-secret-key-2026';
let db; // Sẽ được gán sau khi initDatabase() hoàn tất

// ============================================================
// Middleware
// ============================================================
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ============================================================
// JWT Authentication Middleware
// ============================================================
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: 'Token không hợp lệ hoặc không được cung cấp' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ success: false, message: 'Token hết hạn hoặc không hợp lệ' });
  }
}

// Middleware kiểm tra quyền admin
function adminMiddleware(req, res, next) {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ success: false, message: 'Bạn không có quyền thực hiện thao tác này' });
  }
  next();
}

// ============================================================
// Helper: Phân trang
// ============================================================
function paginate(query, countQuery, params, page = 1, perPage = 20) {
  page = Math.max(1, parseInt(page) || 1);
  perPage = Math.min(100, Math.max(1, parseInt(perPage) || 20));

  const total = db.prepare(countQuery).get(params).total;
  const totalPages = Math.ceil(total / perPage);
  const offset = (page - 1) * perPage;

  const data = db.prepare(`${query} LIMIT ? OFFSET ?`).all(...Object.values(params), perPage, offset);

  return {
    data,
    pagination: { page, per_page: perPage, total, total_pages: totalPages }
  };
}

// ============================================================
// API: Authentication
// ============================================================

// Đăng nhập
app.post('/api/auth/login', (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ success: false, message: 'Vui lòng nhập tên đăng nhập và mật khẩu' });
    }

    const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
    if (!user) {
      return res.status(401).json({ success: false, message: 'Tên đăng nhập hoặc mật khẩu không đúng' });
    }

    const validPassword = bcrypt.compareSync(password, user.password_hash);
    if (!validPassword) {
      return res.status(401).json({ success: false, message: 'Tên đăng nhập hoặc mật khẩu không đúng' });
    }

    // Tạo JWT token (hết hạn sau 7 ngày)
    const token = jwt.sign(
      { id: user.id, username: user.username, full_name: user.full_name, role: user.role, avatar_color: user.avatar_color },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    const { password_hash, ...safeUser } = user;
    res.json({ success: true, data: { token, user: safeUser } });
  } catch (err) {
    console.error('[Auth Login Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Lấy thông tin user hiện tại
app.get('/api/auth/me', authMiddleware, (req, res) => {
  try {
    const user = db.prepare('SELECT id, username, full_name, role, avatar_color, created_at FROM users WHERE id = ?').get(req.user.id);
    if (!user) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy người dùng' });
    }
    res.json({ success: true, data: { user } });
  } catch (err) {
    console.error('[Auth Me Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Users (chỉ admin)
// ============================================================

// Lấy danh sách users
app.get('/api/users', authMiddleware, (req, res) => {
  try {
    const users = db.prepare('SELECT id, username, full_name, role, avatar_color, created_at FROM users ORDER BY id').all();
    res.json({ success: true, data: users });
  } catch (err) {
    console.error('[Users List Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Tạo user mới
app.post('/api/users', authMiddleware, adminMiddleware, (req, res) => {
  try {
    const { username, password, full_name, role, avatar_color } = req.body;

    if (!username || !password || !full_name) {
      return res.status(400).json({ success: false, message: 'Thiếu thông tin bắt buộc' });
    }

    // Kiểm tra username đã tồn tại
    const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
    if (existing) {
      return res.status(400).json({ success: false, message: 'Tên đăng nhập đã tồn tại' });
    }

    const password_hash = bcrypt.hashSync(password, 10);
    const result = db.prepare(
      'INSERT INTO users (username, password_hash, full_name, role, avatar_color) VALUES (?, ?, ?, ?, ?)'
    ).run(username, password_hash, full_name, role || 'employee', avatar_color || '#667eea');

    const user = db.prepare('SELECT id, username, full_name, role, avatar_color, created_at FROM users WHERE id = ?').get(result.lastInsertRowid);
    res.json({ success: true, data: user });
  } catch (err) {
    console.error('[Users Create Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Cập nhật user
app.put('/api/users/:id', authMiddleware, adminMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const { full_name, role, avatar_color, password } = req.body;

    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(id);
    if (!user) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy người dùng' });
    }

    // Cập nhật từng trường nếu có
    if (full_name) db.prepare('UPDATE users SET full_name = ? WHERE id = ?').run(full_name, id);
    if (role) db.prepare('UPDATE users SET role = ? WHERE id = ?').run(role, id);
    if (avatar_color) db.prepare('UPDATE users SET avatar_color = ? WHERE id = ?').run(avatar_color, id);
    if (password) {
      const hash = bcrypt.hashSync(password, 10);
      db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(hash, id);
    }

    const updated = db.prepare('SELECT id, username, full_name, role, avatar_color, created_at FROM users WHERE id = ?').get(id);
    res.json({ success: true, data: updated });
  } catch (err) {
    console.error('[Users Update Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Xóa user
app.delete('/api/users/:id', authMiddleware, adminMiddleware, (req, res) => {
  try {
    const { id } = req.params;

    // Không cho xóa chính mình
    if (parseInt(id) === req.user.id) {
      return res.status(400).json({ success: false, message: 'Không thể xóa tài khoản đang đăng nhập' });
    }

    const user = db.prepare('SELECT id FROM users WHERE id = ?').get(id);
    if (!user) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy người dùng' });
    }

    db.prepare('DELETE FROM users WHERE id = ?').run(id);
    res.json({ success: true, message: 'Đã xóa người dùng' });
  } catch (err) {
    console.error('[Users Delete Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Customers (Khách hàng)
// ============================================================

// Danh sách tất cả khách hàng (cho dropdown select)
app.get('/api/customers/all/list', authMiddleware, (req, res) => {
  try {
    const customers = db.prepare('SELECT id, code, company_name FROM customers ORDER BY code').all();
    res.json({ success: true, data: customers });
  } catch (err) {
    console.error('[Customers All List Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Danh sách khách hàng có phân trang + tìm kiếm
app.get('/api/customers', authMiddleware, (req, res) => {
  try {
    const { search, business_type, page, per_page } = req.query;

    let where = 'WHERE 1=1';
    const params = {};

    // Tìm kiếm theo tên, mã số thuế, SĐT
    if (search) {
      where += ` AND (company_name LIKE @search OR personal_name LIKE @search OR tax_code LIKE @search OR phone LIKE @search OR code LIKE @search)`;
      params.search = `%${search}%`;
    }

    if (business_type) {
      where += ' AND business_type = @business_type';
      params.business_type = business_type;
    }

    const query = `SELECT c.*, u.full_name as created_by_name FROM customers c LEFT JOIN users u ON c.created_by = u.id ${where} ORDER BY c.id DESC`;
    const countQuery = `SELECT COUNT(*) as total FROM customers c ${where}`;

    const result = paginate(query, countQuery, params, page, per_page);
    res.json({ success: true, ...result });
  } catch (err) {
    console.error('[Customers List Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Chi tiết khách hàng (kèm hồ sơ, giao dịch, tổng hợp tài chính)
app.get('/api/customers/:id', authMiddleware, (req, res) => {
  try {
    const customer = db.prepare('SELECT * FROM customers WHERE id = ?').get(req.params.id);
    if (!customer) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy khách hàng' });
    }

    // Lấy danh sách hồ sơ liên quan
    const records = db.prepare(
      `SELECT r.*, u.full_name as assigned_name FROM records r LEFT JOIN users u ON r.assigned_to = u.id WHERE r.customer_id = ? ORDER BY r.id DESC`
    ).all(req.params.id);

    // Lấy danh sách giao dịch liên quan
    const transactions = db.prepare(
      'SELECT * FROM transactions WHERE customer_id = ? ORDER BY transaction_date DESC'
    ).all(req.params.id);

    // Tính tổng thu/chi và công nợ
    const revenue = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE customer_id = ? AND type = 'thu'`
    ).get(req.params.id).total;

    const expense = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE customer_id = ? AND type = 'chi'`
    ).get(req.params.id).total;

    // Công nợ = tổng thu chưa thanh toán
    const debt = db.prepare(
      `SELECT COALESCE(SUM(amount - paid_amount), 0) as total FROM transactions WHERE customer_id = ? AND type = 'thu' AND payment_status != 'da_thanh_toan'`
    ).get(req.params.id).total;

    res.json({
      success: true,
      data: customer,
      records,
      transactions,
      total_revenue: revenue,
      total_expense: expense,
      debt
    });
  } catch (err) {
    console.error('[Customer Detail Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Tạo khách hàng mới
app.post('/api/customers', authMiddleware, (req, res) => {
  try {
    const { company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes } = req.body;

    if (!company_name && !personal_name) {
      return res.status(400).json({ success: false, message: 'Vui lòng nhập tên công ty hoặc tên cá nhân' });
    }

    const code = generateCustomerCode(db);
    const result = db.prepare(`
      INSERT INTO customers (code, company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes, created_by)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(code, company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes, req.user.id);

    const customer = db.prepare('SELECT * FROM customers WHERE id = ?').get(result.lastInsertRowid);
    res.json({ success: true, data: customer });
  } catch (err) {
    console.error('[Customer Create Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Cập nhật khách hàng
app.put('/api/customers/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const customer = db.prepare('SELECT * FROM customers WHERE id = ?').get(id);
    if (!customer) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy khách hàng' });
    }

    const { company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes } = req.body;

    db.prepare(`
      UPDATE customers SET
        company_name = COALESCE(?, company_name),
        personal_name = COALESCE(?, personal_name),
        tax_code = COALESCE(?, tax_code),
        address = COALESCE(?, address),
        representative = COALESCE(?, representative),
        position = COALESCE(?, position),
        phone = COALESCE(?, phone),
        email = COALESCE(?, email),
        business_type = COALESCE(?, business_type),
        notes = COALESCE(?, notes),
        updated_at = datetime('now','localtime')
      WHERE id = ?
    `).run(company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes, id);

    const updated = db.prepare('SELECT * FROM customers WHERE id = ?').get(id);
    res.json({ success: true, data: updated });
  } catch (err) {
    console.error('[Customer Update Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Xóa khách hàng
app.delete('/api/customers/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const customer = db.prepare('SELECT id FROM customers WHERE id = ?').get(id);
    if (!customer) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy khách hàng' });
    }

    // Kiểm tra có hồ sơ liên quan không
    const recordCount = db.prepare('SELECT COUNT(*) as cnt FROM records WHERE customer_id = ?').get(id).cnt;
    if (recordCount > 0) {
      return res.status(400).json({ success: false, message: `Không thể xóa: khách hàng có ${recordCount} hồ sơ liên quan` });
    }

    db.prepare('DELETE FROM transactions WHERE customer_id = ?').run(id);
    db.prepare('DELETE FROM customers WHERE id = ?').run(id);
    res.json({ success: true, message: 'Đã xóa khách hàng' });
  } catch (err) {
    console.error('[Customer Delete Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Records (Hồ sơ)
// ============================================================

// Danh sách hồ sơ có phân trang + tìm kiếm + lọc
app.get('/api/records', authMiddleware, (req, res) => {
  try {
    const { search, type, status, customer_id, assigned_to, date_from, date_to, page, per_page } = req.query;

    let where = 'WHERE 1=1';
    const params = {};

    // Tìm kiếm theo mã hồ sơ, tên khách hàng
    if (search) {
      where += ` AND (r.code LIKE @search OR c.company_name LIKE @search OR c.personal_name LIKE @search)`;
      params.search = `%${search}%`;
    }

    if (type) { where += ' AND r.type = @type'; params.type = type; }
    if (status) { where += ' AND r.status = @status'; params.status = status; }
    if (customer_id) { where += ' AND r.customer_id = @customer_id'; params.customer_id = customer_id; }
    if (assigned_to) { where += ' AND r.assigned_to = @assigned_to'; params.assigned_to = assigned_to; }
    if (date_from) { where += ' AND r.received_date >= @date_from'; params.date_from = date_from; }
    if (date_to) { where += ' AND r.received_date <= @date_to'; params.date_to = date_to; }

    const query = `
      SELECT r.*, 
        c.company_name as customer_name,
        u.full_name as assigned_name
      FROM records r
      LEFT JOIN customers c ON r.customer_id = c.id
      LEFT JOIN users u ON r.assigned_to = u.id
      ${where}
      ORDER BY r.id DESC
    `;

    const countQuery = `
      SELECT COUNT(*) as total FROM records r
      LEFT JOIN customers c ON r.customer_id = c.id
      ${where}
    `;

    const result = paginate(query, countQuery, params, page, per_page);
    res.json({ success: true, ...result });
  } catch (err) {
    console.error('[Records List Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Chi tiết hồ sơ (kèm lịch sử, giao dịch)
app.get('/api/records/:id', authMiddleware, (req, res) => {
  try {
    const record = db.prepare(`
      SELECT r.*, 
        c.company_name as customer_name, c.code as customer_code,
        u.full_name as assigned_name,
        u2.full_name as created_by_name
      FROM records r
      LEFT JOIN customers c ON r.customer_id = c.id
      LEFT JOIN users u ON r.assigned_to = u.id
      LEFT JOIN users u2 ON r.created_by = u2.id
      WHERE r.id = ?
    `).get(req.params.id);

    if (!record) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy hồ sơ' });
    }

    // Lịch sử thay đổi
    const history = db.prepare(
      'SELECT * FROM record_history WHERE record_id = ? ORDER BY created_at DESC'
    ).all(req.params.id);

    // Giao dịch liên quan
    const transactions = db.prepare(
      'SELECT * FROM transactions WHERE record_id = ? ORDER BY transaction_date DESC'
    ).all(req.params.id);

    res.json({ success: true, data: record, history, transactions });
  } catch (err) {
    console.error('[Record Detail Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Tạo hồ sơ mới
app.post('/api/records', authMiddleware, (req, res) => {
  try {
    const { type, customer_id, received_date, deadline, assigned_to, fee_service, fee_state, notes } = req.body;

    if (!type || !customer_id) {
      return res.status(400).json({ success: false, message: 'Vui lòng chọn loại hồ sơ và khách hàng' });
    }

    const code = generateRecordCode(db);
    const result = db.prepare(`
      INSERT INTO records (code, type, customer_id, received_date, deadline, assigned_to, fee_service, fee_state, notes, created_by)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(code, type, customer_id, received_date, deadline, assigned_to, fee_service || 0, fee_state || 0, notes, req.user.id);

    // Ghi lịch sử tạo hồ sơ
    db.prepare(`
      INSERT INTO record_history (record_id, user_id, user_name, action, details)
      VALUES (?, ?, ?, ?, ?)
    `).run(result.lastInsertRowid, req.user.id, req.user.full_name, 'Tạo mới', `Tạo hồ sơ ${code}`);

    const record = db.prepare('SELECT * FROM records WHERE id = ?').get(result.lastInsertRowid);
    res.json({ success: true, data: record });
  } catch (err) {
    console.error('[Record Create Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Cập nhật hồ sơ
app.put('/api/records/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const record = db.prepare('SELECT * FROM records WHERE id = ?').get(id);
    if (!record) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy hồ sơ' });
    }

    const { type, customer_id, received_date, deadline, completed_date, status, assigned_to, fee_service, fee_state, notes } = req.body;

    // Nếu thay đổi trạng thái → ghi lịch sử
    if (status && status !== record.status) {
      const statusLabels = {
        tiep_nhan: 'Tiếp nhận', dang_xu_ly: 'Đang xử lý', cho_nop: 'Chờ nộp',
        da_nop: 'Đã nộp', hoan_thanh: 'Hoàn thành', tra_lai: 'Trả lại'
      };
      const oldLabel = statusLabels[record.status] || record.status;
      const newLabel = statusLabels[status] || status;

      db.prepare(`
        INSERT INTO record_history (record_id, user_id, user_name, action, details)
        VALUES (?, ?, ?, ?, ?)
      `).run(id, req.user.id, req.user.full_name, 'Cập nhật trạng thái', `${oldLabel} → ${newLabel}`);
    }

    // Nếu chuyển sang hoàn thành, tự động cập nhật completed_date
    let finalCompletedDate = completed_date;
    if (status === 'hoan_thanh' && !record.completed_date && !completed_date) {
      finalCompletedDate = new Date().toISOString().split('T')[0];
    }

    db.prepare(`
      UPDATE records SET
        type = COALESCE(?, type),
        customer_id = COALESCE(?, customer_id),
        received_date = COALESCE(?, received_date),
        deadline = COALESCE(?, deadline),
        completed_date = COALESCE(?, completed_date),
        status = COALESCE(?, status),
        assigned_to = COALESCE(?, assigned_to),
        fee_service = COALESCE(?, fee_service),
        fee_state = COALESCE(?, fee_state),
        notes = COALESCE(?, notes),
        updated_at = datetime('now','localtime')
      WHERE id = ?
    `).run(type, customer_id, received_date, deadline, finalCompletedDate, status, assigned_to, fee_service, fee_state, notes, id);

    const updated = db.prepare('SELECT * FROM records WHERE id = ?').get(id);
    res.json({ success: true, data: updated });
  } catch (err) {
    console.error('[Record Update Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Xóa hồ sơ
app.delete('/api/records/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const record = db.prepare('SELECT id FROM records WHERE id = ?').get(id);
    if (!record) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy hồ sơ' });
    }

    // Xóa lịch sử và giao dịch liên quan
    db.prepare('DELETE FROM record_history WHERE record_id = ?').run(id);
    db.prepare('UPDATE transactions SET record_id = NULL WHERE record_id = ?').run(id);
    db.prepare('DELETE FROM records WHERE id = ?').run(id);

    res.json({ success: true, message: 'Đã xóa hồ sơ' });
  } catch (err) {
    console.error('[Record Delete Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Transactions (Giao dịch thu/chi)
// ============================================================

// Danh sách giao dịch có phân trang + tìm kiếm + lọc
app.get('/api/transactions', authMiddleware, (req, res) => {
  try {
    const { search, type, category, payment_status, customer_id, record_id, date_from, date_to, page, per_page } = req.query;

    let where = 'WHERE 1=1';
    const params = {};

    // Tìm kiếm theo mã giao dịch
    if (search) {
      where += ` AND (t.code LIKE @search)`;
      params.search = `%${search}%`;
    }

    if (type) { where += ' AND t.type = @type'; params.type = type; }
    if (category) { where += ' AND t.category = @category'; params.category = category; }
    if (payment_status) { where += ' AND t.payment_status = @payment_status'; params.payment_status = payment_status; }
    if (customer_id) { where += ' AND t.customer_id = @customer_id'; params.customer_id = customer_id; }
    if (record_id) { where += ' AND t.record_id = @record_id'; params.record_id = record_id; }
    if (date_from) { where += ' AND t.transaction_date >= @date_from'; params.date_from = date_from; }
    if (date_to) { where += ' AND t.transaction_date <= @date_to'; params.date_to = date_to; }

    const query = `
      SELECT t.*,
        c.company_name as customer_name,
        r.code as record_code
      FROM transactions t
      LEFT JOIN customers c ON t.customer_id = c.id
      LEFT JOIN records r ON t.record_id = r.id
      ${where}
      ORDER BY t.id DESC
    `;

    const countQuery = `
      SELECT COUNT(*) as total FROM transactions t
      LEFT JOIN customers c ON t.customer_id = c.id
      LEFT JOIN records r ON t.record_id = r.id
      ${where}
    `;

    const result = paginate(query, countQuery, params, page, per_page);
    res.json({ success: true, ...result });
  } catch (err) {
    console.error('[Transactions List Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Chi tiết giao dịch
app.get('/api/transactions/:id', authMiddleware, (req, res) => {
  try {
    const transaction = db.prepare(`
      SELECT t.*,
        c.company_name as customer_name,
        r.code as record_code
      FROM transactions t
      LEFT JOIN customers c ON t.customer_id = c.id
      LEFT JOIN records r ON t.record_id = r.id
      WHERE t.id = ?
    `).get(req.params.id);

    if (!transaction) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy giao dịch' });
    }

    res.json({ success: true, data: transaction });
  } catch (err) {
    console.error('[Transaction Detail Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Tạo giao dịch mới
app.post('/api/transactions', authMiddleware, (req, res) => {
  try {
    const { type, category, amount, transaction_date, record_id, customer_id, payment_status, payment_due_date, paid_amount, notes } = req.body;

    if (!type || !amount) {
      return res.status(400).json({ success: false, message: 'Vui lòng nhập loại và số tiền giao dịch' });
    }

    const code = generateTransactionCode(db);
    const result = db.prepare(`
      INSERT INTO transactions (code, type, category, amount, transaction_date, record_id, customer_id, payment_status, payment_due_date, paid_amount, notes, created_by)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(code, type, category, amount, transaction_date, record_id || null, customer_id || null, payment_status || 'chua_thanh_toan', payment_due_date, paid_amount || 0, notes, req.user.id);

    const transaction = db.prepare('SELECT * FROM transactions WHERE id = ?').get(result.lastInsertRowid);
    res.json({ success: true, data: transaction });
  } catch (err) {
    console.error('[Transaction Create Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Cập nhật giao dịch
app.put('/api/transactions/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const transaction = db.prepare('SELECT * FROM transactions WHERE id = ?').get(id);
    if (!transaction) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy giao dịch' });
    }

    const { type, category, amount, transaction_date, record_id, customer_id, payment_status, payment_due_date, paid_amount, notes } = req.body;

    db.prepare(`
      UPDATE transactions SET
        type = COALESCE(?, type),
        category = COALESCE(?, category),
        amount = COALESCE(?, amount),
        transaction_date = COALESCE(?, transaction_date),
        record_id = ?,
        customer_id = ?,
        payment_status = COALESCE(?, payment_status),
        payment_due_date = ?,
        paid_amount = COALESCE(?, paid_amount),
        notes = COALESCE(?, notes),
        updated_at = datetime('now','localtime')
      WHERE id = ?
    `).run(type, category, amount, transaction_date, record_id !== undefined ? record_id : transaction.record_id, customer_id !== undefined ? customer_id : transaction.customer_id, payment_status, payment_due_date !== undefined ? payment_due_date : transaction.payment_due_date, paid_amount, notes, id);

    const updated = db.prepare(`
      SELECT t.*, c.company_name as customer_name, r.code as record_code
      FROM transactions t
      LEFT JOIN customers c ON t.customer_id = c.id
      LEFT JOIN records r ON t.record_id = r.id
      WHERE t.id = ?
    `).get(id);
    res.json({ success: true, data: updated });
  } catch (err) {
    console.error('[Transaction Update Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Xóa giao dịch
app.delete('/api/transactions/:id', authMiddleware, (req, res) => {
  try {
    const { id } = req.params;
    const transaction = db.prepare('SELECT id FROM transactions WHERE id = ?').get(id);
    if (!transaction) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy giao dịch' });
    }

    db.prepare('DELETE FROM transactions WHERE id = ?').run(id);
    res.json({ success: true, message: 'Đã xóa giao dịch' });
  } catch (err) {
    console.error('[Transaction Delete Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Dashboard
// ============================================================
app.get('/api/dashboard/stats', authMiddleware, (req, res) => {
  try {
    // Tổng hồ sơ
    const totalRecords = db.prepare('SELECT COUNT(*) as cnt FROM records').get().cnt;

    // Hồ sơ đang xử lý (chưa hoàn thành, chưa trả lại)
    const activeRecords = db.prepare(
      `SELECT COUNT(*) as cnt FROM records WHERE status NOT IN ('hoan_thanh', 'tra_lai')`
    ).get().cnt;

    // Hồ sơ đã hoàn thành
    const completedRecords = db.prepare(
      `SELECT COUNT(*) as cnt FROM records WHERE status = 'hoan_thanh'`
    ).get().cnt;

    // Hồ sơ quá hạn (có deadline, chưa hoàn thành, deadline < ngày hiện tại)
    const today = new Date().toISOString().split('T')[0];
    const overdueRecords = db.prepare(
      `SELECT COUNT(*) as cnt FROM records WHERE deadline IS NOT NULL AND deadline < ? AND status NOT IN ('hoan_thanh', 'tra_lai')`
    ).get(today).cnt;

    // Tổng khách hàng
    const totalCustomers = db.prepare('SELECT COUNT(*) as cnt FROM customers').get().cnt;

    // Doanh thu & chi phí tháng hiện tại
    const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM
    const monthlyRevenue = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'thu' AND transaction_date LIKE ?`
    ).get(`${currentMonth}%`).total;

    const monthlyExpense = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'chi' AND transaction_date LIKE ?`
    ).get(`${currentMonth}%`).total;

    // Tổng công nợ (thu chưa thanh toán)
    const totalDebt = db.prepare(
      `SELECT COALESCE(SUM(amount - paid_amount), 0) as total FROM transactions WHERE type = 'thu' AND payment_status != 'da_thanh_toan'`
    ).get().total;

    // Hồ sơ theo trạng thái
    const recordsByStatus = db.prepare(
      `SELECT status, COUNT(*) as count FROM records GROUP BY status`
    ).all();

    // Hồ sơ theo loại
    const recordsByType = db.prepare(
      `SELECT type, COUNT(*) as count FROM records GROUP BY type ORDER BY count DESC`
    ).all();

    // Biểu đồ 12 tháng gần nhất (doanh thu, chi phí, số hồ sơ)
    const monthlyChart = [];
    for (let i = 11; i >= 0; i--) {
      const d = new Date();
      d.setMonth(d.getMonth() - i);
      const month = d.toISOString().slice(0, 7);

      const revenue = db.prepare(
        `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'thu' AND transaction_date LIKE ?`
      ).get(`${month}%`).total;

      const expense = db.prepare(
        `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'chi' AND transaction_date LIKE ?`
      ).get(`${month}%`).total;

      const recordsCount = db.prepare(
        `SELECT COUNT(*) as cnt FROM records WHERE received_date LIKE ?`
      ).get(`${month}%`).cnt;

      monthlyChart.push({ month, revenue, expense, records_count: recordsCount });
    }

    // Deadline sắp tới (top 10 hồ sơ có deadline gần nhất, chưa hoàn thành)
    const upcomingDeadlines = db.prepare(`
      SELECT r.*, c.company_name as customer_name
      FROM records r
      LEFT JOIN customers c ON r.customer_id = c.id
      WHERE r.deadline IS NOT NULL AND r.deadline >= ? AND r.status NOT IN ('hoan_thanh', 'tra_lai')
      ORDER BY r.deadline ASC
      LIMIT 10
    `).all(today);

    // Hoạt động gần đây (20 mục lịch sử mới nhất)
    const recentActivities = db.prepare(`
      SELECT rh.*, r.code as record_code
      FROM record_history rh
      LEFT JOIN records r ON rh.record_id = r.id
      ORDER BY rh.created_at DESC
      LIMIT 20
    `).all();

    // Danh sách hồ sơ quá hạn
    const overdueList = db.prepare(`
      SELECT r.*, c.company_name as customer_name, u.full_name as assigned_name
      FROM records r
      LEFT JOIN customers c ON r.customer_id = c.id
      LEFT JOIN users u ON r.assigned_to = u.id
      WHERE r.deadline IS NOT NULL AND r.deadline < ? AND r.status NOT IN ('hoan_thanh', 'tra_lai')
      ORDER BY r.deadline ASC
    `).all(today);

    res.json({
      success: true,
      data: {
        total_records: totalRecords,
        active_records: activeRecords,
        completed_records: completedRecords,
        overdue_records: overdueRecords,
        total_customers: totalCustomers,
        monthly_revenue: monthlyRevenue,
        monthly_expense: monthlyExpense,
        total_debt: totalDebt,
        records_by_status: recordsByStatus,
        records_by_type: recordsByType,
        monthly_chart: monthlyChart,
        upcoming_deadlines: upcomingDeadlines,
        recent_activities: recentActivities,
        overdue_list: overdueList
      }
    });
  } catch (err) {
    console.error('[Dashboard Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Reports (Báo cáo)
// ============================================================

// Báo cáo tài chính
app.get('/api/reports/finance', authMiddleware, (req, res) => {
  try {
    const { period, year, month, quarter } = req.query;
    const y = parseInt(year) || new Date().getFullYear();

    let dateFilter = '';
    const params = {};

    if (period === 'monthly' && month) {
      const m = String(month).padStart(2, '0');
      dateFilter = `AND transaction_date LIKE @monthPattern`;
      params.monthPattern = `${y}-${m}%`;
    } else if (period === 'quarterly' && quarter) {
      const q = parseInt(quarter);
      const startMonth = (q - 1) * 3 + 1;
      const endMonth = q * 3;
      dateFilter = `AND transaction_date >= @qStart AND transaction_date <= @qEnd`;
      params.qStart = `${y}-${String(startMonth).padStart(2, '0')}-01`;
      params.qEnd = `${y}-${String(endMonth).padStart(2, '0')}-31`;
    } else {
      // Cả năm
      dateFilter = `AND transaction_date LIKE @yearPattern`;
      params.yearPattern = `${y}-%`;
    }

    // Tổng thu/chi/lợi nhuận
    const revenue = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'thu' ${dateFilter}`
    ).get(params).total;

    const expense = db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'chi' ${dateFilter}`
    ).get(params).total;

    // Phân loại theo danh mục
    const byCategory = db.prepare(
      `SELECT category, COALESCE(SUM(amount), 0) as total FROM transactions WHERE 1=1 ${dateFilter} GROUP BY category ORDER BY total DESC`
    ).all(params);

    // Phân loại theo tháng (cả năm)
    const byMonth = [];
    for (let m = 1; m <= 12; m++) {
      const monthStr = `${y}-${String(m).padStart(2, '0')}`;
      const mRevenue = db.prepare(
        `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'thu' AND transaction_date LIKE ?`
      ).get(`${monthStr}%`).total;
      const mExpense = db.prepare(
        `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'chi' AND transaction_date LIKE ?`
      ).get(`${monthStr}%`).total;
      byMonth.push({ month: monthStr, revenue: mRevenue, expense: mExpense });
    }

    // Danh sách giao dịch trong kỳ
    const transactions = db.prepare(
      `SELECT t.*, c.company_name as customer_name, r.code as record_code
       FROM transactions t
       LEFT JOIN customers c ON t.customer_id = c.id
       LEFT JOIN records r ON t.record_id = r.id
       WHERE 1=1 ${dateFilter}
       ORDER BY t.transaction_date DESC`
    ).all(params);

    res.json({
      success: true,
      data: {
        summary: { revenue, expense, profit: revenue - expense },
        by_category: byCategory,
        by_month: byMonth,
        transactions
      }
    });
  } catch (err) {
    console.error('[Report Finance Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Báo cáo hồ sơ
app.get('/api/reports/records', authMiddleware, (req, res) => {
  try {
    const { year, assigned_to } = req.query;
    const y = parseInt(year) || new Date().getFullYear();

    let assignFilter = '';
    const params = {};

    if (assigned_to) {
      assignFilter = ' AND r.assigned_to = @assigned_to';
      params.assigned_to = assigned_to;
    }

    // Hồ sơ theo tháng
    const byMonth = [];
    for (let m = 1; m <= 12; m++) {
      const monthStr = `${y}-${String(m).padStart(2, '0')}`;
      const count = db.prepare(
        `SELECT COUNT(*) as cnt FROM records r WHERE r.received_date LIKE @monthStr ${assignFilter}`
      ).get({ ...params, monthStr: `${monthStr}%` }).cnt;
      byMonth.push({ month: monthStr, count });
    }

    // Hồ sơ theo loại
    const byType = db.prepare(
      `SELECT r.type, COUNT(*) as count FROM records r WHERE r.received_date LIKE @yearPattern ${assignFilter} GROUP BY r.type ORDER BY count DESC`
    ).all({ ...params, yearPattern: `${y}-%` });

    // Hồ sơ theo trạng thái
    const byStatus = db.prepare(
      `SELECT r.status, COUNT(*) as count FROM records r WHERE r.received_date LIKE @yearPattern ${assignFilter} GROUP BY r.status`
    ).all({ ...params, yearPattern: `${y}-%` });

    // Hồ sơ theo nhân viên
    const byEmployee = db.prepare(`
      SELECT 
        u.full_name as name,
        COUNT(*) as total,
        SUM(CASE WHEN r.status = 'hoan_thanh' THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN r.status NOT IN ('hoan_thanh', 'tra_lai') THEN 1 ELSE 0 END) as in_progress
      FROM records r
      LEFT JOIN users u ON r.assigned_to = u.id
      WHERE r.received_date LIKE @yearPattern ${assignFilter}
      GROUP BY r.assigned_to
      ORDER BY total DESC
    `).all({ ...params, yearPattern: `${y}-%` });

    res.json({
      success: true,
      data: { by_month: byMonth, by_type: byType, by_status: byStatus, by_employee: byEmployee }
    });
  } catch (err) {
    console.error('[Report Records Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Notifications (Thông báo)
// ============================================================

// Lấy danh sách thông báo của user hiện tại
app.get('/api/notifications', authMiddleware, (req, res) => {
  try {
    const notifications = db.prepare(
      'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50'
    ).all(req.user.id);

    const unreadCount = db.prepare(
      'SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0'
    ).get(req.user.id).cnt;

    res.json({ success: true, data: notifications, unread_count: unreadCount });
  } catch (err) {
    console.error('[Notifications Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Đánh dấu đã đọc 1 thông báo
app.put('/api/notifications/:id/read', authMiddleware, (req, res) => {
  try {
    db.prepare('UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?').run(req.params.id, req.user.id);
    res.json({ success: true });
  } catch (err) {
    console.error('[Notification Read Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Đánh dấu đã đọc tất cả
app.put('/api/notifications/read-all', authMiddleware, (req, res) => {
  try {
    db.prepare('UPDATE notifications SET is_read = 1 WHERE user_id = ?').run(req.user.id);
    res.json({ success: true });
  } catch (err) {
    console.error('[Notifications Read All Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// ============================================================
// API: Data Export/Import
// ============================================================

// Xuất toàn bộ dữ liệu
app.get('/api/data/export', authMiddleware, (req, res) => {
  try {
    const customers = db.prepare('SELECT * FROM customers ORDER BY id').all();
    const records = db.prepare('SELECT * FROM records ORDER BY id').all();
    const transactions = db.prepare('SELECT * FROM transactions ORDER BY id').all();

    res.json({
      success: true,
      data: {
        exported_at: new Date().toISOString(),
        customers,
        records,
        transactions
      }
    });
  } catch (err) {
    console.error('[Data Export Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi hệ thống' });
  }
});

// Nhập dữ liệu
app.post('/api/data/import', authMiddleware, adminMiddleware, (req, res) => {
  try {
    const { customers, records, transactions } = req.body;
    let stats = { customers: 0, records: 0, transactions: 0 };

    // Sử dụng transaction để đảm bảo tính toàn vẹn dữ liệu
    const importData = db.transaction(() => {
      // Nhập khách hàng
      if (customers && Array.isArray(customers)) {
        const insertCustomer = db.prepare(`
          INSERT OR IGNORE INTO customers (code, company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes, created_by, created_at, updated_at)
          VALUES (@code, @company_name, @personal_name, @tax_code, @address, @representative, @position, @phone, @email, @business_type, @notes, @created_by, @created_at, @updated_at)
        `);
        for (const c of customers) {
          const result = insertCustomer.run(c);
          if (result.changes > 0) stats.customers++;
        }
      }

      // Nhập hồ sơ
      if (records && Array.isArray(records)) {
        const insertRecord = db.prepare(`
          INSERT OR IGNORE INTO records (code, type, customer_id, received_date, deadline, completed_date, status, assigned_to, fee_service, fee_state, notes, created_by, created_at, updated_at)
          VALUES (@code, @type, @customer_id, @received_date, @deadline, @completed_date, @status, @assigned_to, @fee_service, @fee_state, @notes, @created_by, @created_at, @updated_at)
        `);
        for (const r of records) {
          const result = insertRecord.run(r);
          if (result.changes > 0) stats.records++;
        }
      }

      // Nhập giao dịch
      if (transactions && Array.isArray(transactions)) {
        const insertTransaction = db.prepare(`
          INSERT OR IGNORE INTO transactions (code, type, category, amount, transaction_date, record_id, customer_id, payment_status, payment_due_date, paid_amount, notes, created_by, created_at, updated_at)
          VALUES (@code, @type, @category, @amount, @transaction_date, @record_id, @customer_id, @payment_status, @payment_due_date, @paid_amount, @notes, @created_by, @created_at, @updated_at)
        `);
        for (const t of transactions) {
          const result = insertTransaction.run(t);
          if (result.changes > 0) stats.transactions++;
        }
      }
    });

    importData();
    res.json({ success: true, stats, message: 'Đã nhập dữ liệu thành công' });
  } catch (err) {
    console.error('[Data Import Error]', err);
    res.status(500).json({ success: false, message: 'Lỗi khi nhập dữ liệu' });
  }
});

// ============================================================
// Seed Data - Dữ liệu mẫu khi khởi động lần đầu
// ============================================================
function seedData() {
  // Chỉ seed khi bảng users trống (lần chạy đầu tiên)
  const userCount = db.prepare('SELECT COUNT(*) as cnt FROM users').get().cnt;
  if (userCount > 0) {
    console.log('[Seed] Database đã có dữ liệu, bỏ qua seed.');
    return;
  }

  console.log('[Seed] Đang tạo dữ liệu mẫu...');

  const seed = db.transaction(() => {
    // ---- Users (3 người dùng) ----
    const insertUser = db.prepare(
      'INSERT INTO users (username, password_hash, full_name, role, avatar_color) VALUES (?, ?, ?, ?, ?)'
    );
    insertUser.run('admin', bcrypt.hashSync('admin123', 10), 'Nguyễn Văn Admin', 'admin', '#667eea');
    insertUser.run('huong', bcrypt.hashSync('nv123', 10), 'Trần Thị Hương', 'employee', '#f59e0b');
    insertUser.run('minh', bcrypt.hashSync('nv123', 10), 'Lê Văn Minh', 'employee', '#10b981');

    // ---- Customers (6 khách hàng) ----
    const insertCustomer = db.prepare(`
      INSERT INTO customers (code, company_name, personal_name, tax_code, address, representative, position, phone, email, business_type, notes, created_by, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    insertCustomer.run('KH-0001', 'Công ty TNHH Thương Mại ABC', null, '0312345678',
      '123 Nguyễn Huệ, P. Bến Nghé, Q.1, TP.HCM', 'Nguyễn Văn An', 'Giám đốc',
      '0901234567', 'an@abc.com.vn', 'tnhh_2tv', 'Khách hàng lâu năm', 1, '2026-01-05 09:00:00');

    insertCustomer.run('KH-0002', 'Công ty CP Công Nghệ XYZ', null, '0398765432',
      '456 Lê Lợi, P. Bến Thành, Q.1, TP.HCM', 'Trần Thị Bình', 'Chủ tịch HĐQT',
      '0912345678', 'binh@xyz.vn', 'co_phan', 'Công ty công nghệ', 1, '2026-01-10 10:30:00');

    insertCustomer.run('KH-0003', 'Công ty TNHH MTV Hoàng Gia', null, '0356789012',
      '789 Cách Mạng Tháng 8, P.6, Q.3, TP.HCM', 'Lê Hoàng Cường', 'Chủ sở hữu',
      '0923456789', 'cuong@hoanggia.vn', 'tnhh_1tv', null, 1, '2026-02-01 08:00:00');

    insertCustomer.run('KH-0004', 'Công ty CP Đầu Tư Phát Triển DEF', null, '0387654321',
      '321 Trần Hưng Đạo, P. Nguyễn Cư Trinh, Q.1, TP.HCM', 'Phạm Thị Dung', 'Tổng Giám đốc',
      '0934567890', 'dung@def.com.vn', 'co_phan', 'Công ty đầu tư BĐS', 1, '2026-02-15 14:00:00');

    insertCustomer.run('KH-0005', 'Hộ KD Minh Tâm', 'Võ Minh Tâm', '8901234567',
      '55 Phan Đình Phùng, P.1, Q. Phú Nhuận, TP.HCM', 'Võ Minh Tâm', 'Chủ hộ',
      '0945678901', 'minhtam@gmail.com', 'ho_kinh_doanh', 'Hộ kinh doanh thực phẩm', 2, '2026-03-01 09:15:00');

    insertCustomer.run('KH-0006', 'Công ty TNHH SX Thái Bình', null, '0323456789',
      '88 Hai Bà Trưng, P. Đa Kao, Q.1, TP.HCM', 'Đỗ Thái Bình', 'Giám đốc',
      '0956789012', 'binh@thaibinhsx.vn', 'tnhh_2tv', 'Sản xuất bao bì', 1, '2026-03-10 11:00:00');

    // ---- Records (10 hồ sơ) ----
    const insertRecord = db.prepare(`
      INSERT INTO records (code, type, customer_id, received_date, deadline, completed_date, status, assigned_to, fee_service, fee_state, notes, created_by, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    // 1. Thành lập TNHH 2TV - Hoàn thành
    insertRecord.run('HS-2026-0001', 'thanh_lap_tnhh_2tv', 1, '2026-01-10', '2026-01-25', '2026-01-22', 'hoan_thanh', 2, 5000000, 500000, 'Hồ sơ thành lập công ty ABC', 1, '2026-01-10 09:00:00');

    // 2. Thành lập Cổ phần - Hoàn thành
    insertRecord.run('HS-2026-0002', 'thanh_lap_co_phan', 2, '2026-01-15', '2026-02-05', '2026-02-02', 'hoan_thanh', 3, 8000000, 1000000, 'Thành lập CP XYZ', 1, '2026-01-15 10:00:00');

    // 3. Thay đổi địa chỉ - Đã nộp
    insertRecord.run('HS-2026-0003', 'thay_doi_dia_chi', 3, '2026-02-10', '2026-02-28', null, 'da_nop', 2, 2000000, 300000, 'Chuyển trụ sở Q.3 sang Q.7', 1, '2026-02-10 14:30:00');

    // 4. Tăng vốn TNHH 2TV - Đang xử lý
    insertRecord.run('HS-2026-0004', 'tang_von_tnhh_2tv', 1, '2026-03-05', '2026-03-25', null, 'dang_xu_ly', 3, 3000000, 300000, 'Tăng vốn từ 1 tỷ lên 3 tỷ', 1, '2026-03-05 08:45:00');

    // 5. Thành lập ĐĐKD - Hoàn thành
    insertRecord.run('HS-2026-0005', 'thanh_lap_ddkd', 5, '2026-03-15', '2026-03-30', '2026-03-28', 'hoan_thanh', 2, 1500000, 100000, 'Đăng ký hộ KD thực phẩm', 2, '2026-03-15 09:30:00');

    // 6. Chuyển nhượng - Chờ nộp
    insertRecord.run('HS-2026-0006', 'chuyen_nhuong', 4, '2026-04-01', '2026-04-20', null, 'cho_nop', 3, 4000000, 500000, 'Chuyển nhượng 30% CP', 1, '2026-04-01 10:00:00');

    // 7. Thay đổi ngành nghề - Tiếp nhận
    insertRecord.run('HS-2026-0007', 'thay_doi_nganh_nghe', 6, '2026-04-20', '2026-05-10', null, 'tiep_nhan', 2, 2500000, 300000, 'Bổ sung ngành nghề sản xuất', 1, '2026-04-20 15:00:00');

    // 8. Giải thể TNHH 1TV - Đang xử lý
    insertRecord.run('HS-2026-0008', 'giai_the_tnhh_1tv', 3, '2026-05-05', '2026-06-05', null, 'dang_xu_ly', 3, 3500000, 200000, 'Giải thể Hoàng Gia', 1, '2026-05-05 11:00:00');

    // 9. Tạm dừng Cổ phần - Đã nộp (deadline gần - dùng cho test thông báo)
    insertRecord.run('HS-2026-0009', 'tam_dung_co_phan', 4, '2026-05-20', '2026-06-25', null, 'da_nop', 2, 2000000, 200000, 'Tạm dừng hoạt động DEF', 1, '2026-05-20 08:00:00');

    // 10. Thay đổi người đại diện - Tiếp nhận (deadline quá hạn - dùng cho test thông báo)
    insertRecord.run('HS-2026-0010', 'thay_doi_nguoi_dai_dien', 6, '2026-06-01', '2026-06-20', null, 'tiep_nhan', 3, 2000000, 300000, 'Đổi giám đốc Thái Bình', 1, '2026-06-01 09:00:00');

    // ---- Transactions (15 giao dịch thu/chi) ----
    const insertTransaction = db.prepare(`
      INSERT INTO transactions (code, type, category, amount, transaction_date, record_id, customer_id, payment_status, payment_due_date, paid_amount, notes, created_by, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    // Thu từ hồ sơ 1 - ABC
    insertTransaction.run('GD-0001', 'thu', 'phi_dich_vu', 5000000, '2026-01-12', 1, 1, 'da_thanh_toan', '2026-01-20', 5000000, 'Phí DV thành lập ABC', 1, '2026-01-12 09:00:00');
    insertTransaction.run('GD-0002', 'chi', 'le_phi_nha_nuoc', 500000, '2026-01-15', 1, 1, 'da_thanh_toan', null, 500000, 'Lệ phí nhà nước HS-2026-0001', 1, '2026-01-15 10:00:00');

    // Thu từ hồ sơ 2 - XYZ
    insertTransaction.run('GD-0003', 'thu', 'phi_dich_vu', 8000000, '2026-01-20', 2, 2, 'da_thanh_toan', '2026-02-01', 8000000, 'Phí DV thành lập CP XYZ', 1, '2026-01-20 14:00:00');
    insertTransaction.run('GD-0004', 'chi', 'le_phi_nha_nuoc', 1000000, '2026-01-25', 2, 2, 'da_thanh_toan', null, 1000000, 'Lệ phí nhà nước CP XYZ', 1, '2026-01-25 09:00:00');
    insertTransaction.run('GD-0005', 'chi', 'phi_cong_chung', 500000, '2026-01-28', 2, 2, 'da_thanh_toan', null, 500000, 'Công chứng điều lệ XYZ', 1, '2026-01-28 11:00:00');

    // Thu từ hồ sơ 3 - Hoàng Gia
    insertTransaction.run('GD-0006', 'thu', 'phi_dich_vu', 2000000, '2026-02-12', 3, 3, 'thanh_toan_mot_phan', '2026-03-01', 1000000, 'Phí thay đổi địa chỉ HG (đã TT 50%)', 1, '2026-02-12 10:00:00');
    insertTransaction.run('GD-0007', 'chi', 'le_phi_nha_nuoc', 300000, '2026-02-15', 3, 3, 'da_thanh_toan', null, 300000, 'Lệ phí thay đổi địa chỉ', 2, '2026-02-15 08:30:00');

    // Thu từ hồ sơ 4 - ABC tăng vốn
    insertTransaction.run('GD-0008', 'thu', 'phi_dich_vu', 3000000, '2026-03-06', 4, 1, 'chua_thanh_toan', '2026-03-30', 0, 'Phí tăng vốn ABC - chưa TT', 1, '2026-03-06 09:00:00');

    // Thu từ hồ sơ 5 - Minh Tâm
    insertTransaction.run('GD-0009', 'thu', 'phi_dich_vu', 1500000, '2026-03-16', 5, 5, 'da_thanh_toan', '2026-03-25', 1500000, 'Phí thành lập HKD Minh Tâm', 2, '2026-03-16 10:00:00');
    insertTransaction.run('GD-0010', 'chi', 'le_phi_nha_nuoc', 100000, '2026-03-18', 5, 5, 'da_thanh_toan', null, 100000, 'Lệ phí ĐĐKD Minh Tâm', 2, '2026-03-18 09:00:00');

    // Chi phí văn phòng chung
    insertTransaction.run('GD-0011', 'chi', 'chi_phi_in_an', 350000, '2026-04-05', null, null, 'da_thanh_toan', null, 350000, 'In ấn hồ sơ tháng 4', 1, '2026-04-05 14:00:00');
    insertTransaction.run('GD-0012', 'chi', 'van_chuyen', 200000, '2026-04-10', null, null, 'da_thanh_toan', null, 200000, 'Phí giao hồ sơ tháng 4', 2, '2026-04-10 16:00:00');

    // Thu từ hồ sơ 6 - DEF chuyển nhượng
    insertTransaction.run('GD-0013', 'thu', 'phi_dich_vu', 4000000, '2026-04-03', 6, 4, 'thanh_toan_mot_phan', '2026-04-30', 2000000, 'Phí CN DEF - đã TT 50%', 1, '2026-04-03 09:30:00');

    // Thu từ hồ sơ 7 - Thái Bình
    insertTransaction.run('GD-0014', 'thu', 'phi_dich_vu', 2500000, '2026-04-22', 7, 6, 'chua_thanh_toan', '2026-05-15', 0, 'Phí TĐ ngành nghề TB - chưa TT', 1, '2026-04-22 15:30:00');

    // Chi phí nhân công
    insertTransaction.run('GD-0015', 'chi', 'nhan_cong', 800000, '2026-05-10', 8, 3, 'da_thanh_toan', null, 800000, 'Chi phí nhân công giải thể HG', 3, '2026-05-10 10:00:00');

    // ---- Notifications (thông báo mẫu) ----
    const insertNotification = db.prepare(`
      INSERT INTO notifications (user_id, title, message, type, is_read, record_id, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    insertNotification.run(1, 'Hồ sơ hoàn thành', 'Hồ sơ HS-2026-0001 đã được hoàn thành bởi Trần Thị Hương', 'success', 1, 1, '2026-01-22 16:00:00');
    insertNotification.run(2, 'Hồ sơ mới được giao', 'Bạn được giao hồ sơ HS-2026-0003 - Thay đổi địa chỉ Hoàng Gia', 'info', 1, 3, '2026-02-10 14:35:00');
    insertNotification.run(1, 'Công nợ chưa thu', 'Khách hàng ABC chưa thanh toán phí tăng vốn 3.000.000₫', 'warning', 0, 4, '2026-04-01 09:00:00');
    insertNotification.run(3, 'Hồ sơ mới được giao', 'Bạn được giao hồ sơ HS-2026-0008 - Giải thể Hoàng Gia', 'info', 0, 8, '2026-05-05 11:05:00');

    // ---- Record History (lịch sử thay đổi mẫu) ----
    const insertHistory = db.prepare(`
      INSERT INTO record_history (record_id, user_id, user_name, action, details, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    insertHistory.run(1, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0001', '2026-01-10 09:00:00');
    insertHistory.run(1, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Tiếp nhận → Đang xử lý', '2026-01-12 09:30:00');
    insertHistory.run(1, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Đang xử lý → Chờ nộp', '2026-01-18 14:00:00');
    insertHistory.run(1, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Chờ nộp → Đã nộp', '2026-01-19 10:00:00');
    insertHistory.run(1, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Đã nộp → Hoàn thành', '2026-01-22 16:00:00');

    insertHistory.run(2, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0002', '2026-01-15 10:00:00');
    insertHistory.run(2, 3, 'Lê Văn Minh', 'Cập nhật trạng thái', 'Tiếp nhận → Đang xử lý', '2026-01-17 08:00:00');
    insertHistory.run(2, 3, 'Lê Văn Minh', 'Cập nhật trạng thái', 'Đang xử lý → Hoàn thành', '2026-02-02 15:30:00');

    insertHistory.run(3, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0003', '2026-02-10 14:30:00');
    insertHistory.run(3, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Tiếp nhận → Đang xử lý', '2026-02-12 09:00:00');
    insertHistory.run(3, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Đang xử lý → Đã nộp', '2026-02-25 11:00:00');

    insertHistory.run(4, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0004', '2026-03-05 08:45:00');
    insertHistory.run(4, 3, 'Lê Văn Minh', 'Cập nhật trạng thái', 'Tiếp nhận → Đang xử lý', '2026-03-08 10:00:00');

    insertHistory.run(5, 2, 'Trần Thị Hương', 'Tạo mới', 'Tạo hồ sơ HS-2026-0005', '2026-03-15 09:30:00');
    insertHistory.run(5, 2, 'Trần Thị Hương', 'Cập nhật trạng thái', 'Tiếp nhận → Hoàn thành', '2026-03-28 16:00:00');

    insertHistory.run(6, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0006', '2026-04-01 10:00:00');
    insertHistory.run(7, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0007', '2026-04-20 15:00:00');
    insertHistory.run(8, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0008', '2026-05-05 11:00:00');
    insertHistory.run(9, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0009', '2026-05-20 08:00:00');
    insertHistory.run(10, 1, 'Nguyễn Văn Admin', 'Tạo mới', 'Tạo hồ sơ HS-2026-0010', '2026-06-01 09:00:00');
  });

  seed();
  console.log('[Seed] ✅ Đã tạo dữ liệu mẫu: 3 users, 6 customers, 10 records, 15 transactions');
}

// ============================================================
// Kiểm tra Deadline - Tạo thông báo cho hồ sơ sắp/quá hạn
// ============================================================
function checkDeadlines() {
  console.log('[Deadline] Kiểm tra deadline hồ sơ...');

  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];

  // Tính ngày 3 ngày sau
  const threeDaysLater = new Date(today);
  threeDaysLater.setDate(threeDaysLater.getDate() + 3);
  const threeDaysStr = threeDaysLater.toISOString().split('T')[0];

  // Hồ sơ quá hạn (deadline < today, chưa hoàn thành)
  const overdueRecords = db.prepare(`
    SELECT r.*, c.company_name as customer_name
    FROM records r
    LEFT JOIN customers c ON r.customer_id = c.id
    WHERE r.deadline IS NOT NULL 
      AND r.deadline < ?
      AND r.status NOT IN ('hoan_thanh', 'tra_lai')
  `).all(todayStr);

  // Hồ sơ sắp hết hạn (deadline trong 3 ngày tới)
  const upcomingRecords = db.prepare(`
    SELECT r.*, c.company_name as customer_name
    FROM records r
    LEFT JOIN customers c ON r.customer_id = c.id
    WHERE r.deadline IS NOT NULL 
      AND r.deadline >= ?
      AND r.deadline <= ?
      AND r.status NOT IN ('hoan_thanh', 'tra_lai')
  `).all(todayStr, threeDaysStr);

  // Lấy tất cả user để gửi thông báo
  const users = db.prepare('SELECT id FROM users').all();

  const insertNotif = db.prepare(`
    INSERT INTO notifications (user_id, title, message, type, record_id)
    VALUES (?, ?, ?, ?, ?)
  `);

  let count = 0;

  // Tạo thông báo cho hồ sơ quá hạn
  for (const record of overdueRecords) {
    const daysOverdue = Math.ceil((today - new Date(record.deadline)) / (1000 * 60 * 60 * 24));
    for (const user of users) {
      // Kiểm tra chưa có thông báo trùng ngày hôm nay
      const existing = db.prepare(
        `SELECT id FROM notifications WHERE record_id = ? AND user_id = ? AND title LIKE '%quá hạn%' AND created_at LIKE ?`
      ).get(record.id, user.id, `${todayStr}%`);

      if (!existing) {
        insertNotif.run(
          user.id,
          '⚠️ Hồ sơ quá hạn',
          `Hồ sơ ${record.code} (${record.customer_name || 'N/A'}) đã quá hạn ${daysOverdue} ngày`,
          'warning',
          record.id
        );
        count++;
      }
    }
  }

  // Tạo thông báo cho hồ sơ sắp hết hạn
  for (const record of upcomingRecords) {
    const daysLeft = Math.ceil((new Date(record.deadline) - today) / (1000 * 60 * 60 * 24));
    for (const user of users) {
      const existing = db.prepare(
        `SELECT id FROM notifications WHERE record_id = ? AND user_id = ? AND title LIKE '%sắp hết hạn%' AND created_at LIKE ?`
      ).get(record.id, user.id, `${todayStr}%`);

      if (!existing) {
        insertNotif.run(
          user.id,
          '🕐 Hồ sơ sắp hết hạn',
          `Hồ sơ ${record.code} (${record.customer_name || 'N/A'}) còn ${daysLeft} ngày nữa hết hạn (${record.deadline})`,
          'info',
          record.id
        );
        count++;
      }
    }
  }

  console.log(`[Deadline] ✅ Đã kiểm tra: ${overdueRecords.length} quá hạn, ${upcomingRecords.length} sắp hết hạn, tạo ${count} thông báo mới`);
}

// ============================================================
// Catch-all: SPA fallback
// ============================================================
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ============================================================
// Khởi động server
// ============================================================
// ============================================================
// Khởi động server (async để chờ sql.js khởi tạo)
// ============================================================
async function startServer() {
  try {
    db = await initDatabase();
    console.log('[Server] Database đã sẵn sàng');

    app.listen(PORT, () => {
      console.log(`\n🚀 NAC CRM Server đang chạy tại http://localhost:${PORT}`);
      console.log(`📁 Database: ./data/crm.db`);
      console.log(`🔐 JWT Secret: ${JWT_SECRET.substring(0, 10)}...`);
      console.log('');

      // Tạo dữ liệu mẫu nếu lần đầu chạy
      seedData();

      // Kiểm tra deadline mỗi khi khởi động
      checkDeadlines();
    });
  } catch (err) {
    console.error('❌ Lỗi khởi động server:', err);
    process.exit(1);
  }
}

startServer();

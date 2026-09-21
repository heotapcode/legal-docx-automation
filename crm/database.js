/**
 * database.js - Module quản lý cơ sở dữ liệu SQLite cho NAC CRM
 * 
 * Sử dụng sql.js (SQLite biên dịch sang WebAssembly).
 * Tương thích API với better-sqlite3: db.prepare().get(), .all(), .run()
 * Tự động lưu file sau mỗi thay đổi.
 */

const initSqlJs = require('sql.js');
const path = require('path');
const fs = require('fs');

// ============================================================
// Wrapper tương thích API better-sqlite3
// ============================================================

class StatementWrapper {
  constructor(dbWrapper, sql) {
    this._dbW = dbWrapper;
    this._sql = sql;
  }

  _toBindable(args) {
    if (args.length === 0) return undefined;
    if (args.length === 1 && args[0] && typeof args[0] === 'object' && !Array.isArray(args[0])) {
      // Named params: {key: val} → {$key: val}  (sql.js uses $ prefix)
      const obj = {};
      for (const [k, v] of Object.entries(args[0])) {
        // Strip any existing prefix and add $
        const cleanKey = k.replace(/^[@$:]/, '');
        obj['$' + cleanKey] = v;
      }
      return obj;
    }
    return args;
  }

  // Convert @param to $param in SQL (sql.js only supports $ and : prefixes)
  _normalizeSql(sql) {
    return sql.replace(/@(\w+)/g, '$$$1');
  }

  get(...args) {
    let stmt;
    try {
      const sql = this._normalizeSql(this._sql);
      stmt = this._dbW._db.prepare(sql);
      const bind = this._toBindable(args);
      if (bind) stmt.bind(bind);
      if (stmt.step()) {
        const cols = stmt.getColumnNames();
        const vals = stmt.get();
        const row = {};
        cols.forEach((c, i) => row[c] = vals[i]);
        return row;
      }
      return undefined;
    } catch (e) {
      console.error('[DB SQL Error]', this._sql, args, e.message);
      throw e;
    } finally {
      if (stmt) try { stmt.free(); } catch(e) {}
    }
  }

  all(...args) {
    let stmt;
    try {
      const sql = this._normalizeSql(this._sql);
      stmt = this._dbW._db.prepare(sql);
      const bind = this._toBindable(args);
      if (bind) stmt.bind(bind);
      const results = [];
      while (stmt.step()) {
        const cols = stmt.getColumnNames();
        const vals = stmt.get();
        const row = {};
        cols.forEach((c, i) => row[c] = vals[i]);
        results.push(row);
      }
      return results;
    } catch (e) {
      console.error('[DB SQL Error]', this._sql, args, e.message);
      throw e;
    } finally {
      if (stmt) try { stmt.free(); } catch(e) {}
    }
  }

  run(...args) {
    try {
      const sql = this._normalizeSql(this._sql);
      const bind = this._toBindable(args);
      if (bind) {
        this._dbW._db.run(sql, bind);
      } else {
        this._dbW._db.run(sql);
      }
      const changes = this._dbW._db.getRowsModified();
      let lastInsertRowid = 0;
      try {
        const s = this._dbW._db.prepare('SELECT last_insert_rowid() as id');
        if (s.step()) lastInsertRowid = s.get()[0];
        s.free();
      } catch(e) {}
      this._dbW._scheduleSave();
      return { changes, lastInsertRowid };
    } catch (e) {
      console.error('[DB SQL Error]', this._sql, args, e.message);
      throw e;
    }
  }
}

class DatabaseWrapper {
  constructor(sqlDb, filePath) {
    this._db = sqlDb;
    this._filePath = filePath;
    this._saveTimer = null;
  }

  prepare(sql) {
    return new StatementWrapper(this, sql);
  }

  exec(sql) {
    this._db.run(sql);
    this._scheduleSave();
  }

  pragma(str) {
    try { this._db.run(`PRAGMA ${str}`); } catch(e) {}
  }

  transaction(fn) {
    const self = this;
    return function (...args) {
      self._db.run('BEGIN TRANSACTION');
      try {
        const result = fn.apply(this, args);
        self._db.run('COMMIT');
        self._scheduleSave();
        return result;
      } catch (e) {
        self._db.run('ROLLBACK');
        throw e;
      }
    };
  }

  _scheduleSave() {
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => this._saveNow(), 500);
  }

  _saveNow() {
    if (this._saveTimer) { clearTimeout(this._saveTimer); this._saveTimer = null; }
    try {
      const data = this._db.export();
      fs.writeFileSync(this._filePath, Buffer.from(data));
    } catch (e) {
      console.error('[DB] Lỗi lưu database:', e.message);
    }
  }
}

// ============================================================
// Khởi tạo database (async vì sql.js cần load WASM)
// ============================================================
const dataDir = path.join(__dirname, 'data');
const dbPath = path.join(dataDir, 'crm.db');

async function initDatabase() {
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
    console.log('[DB] Đã tạo thư mục data/');
  }

  const SQL = await initSqlJs();
  let sqlDb;

  if (fs.existsSync(dbPath)) {
    const buffer = fs.readFileSync(dbPath);
    sqlDb = new SQL.Database(buffer);
    console.log(`[DB] Đã load database từ: ${dbPath}`);
  } else {
    sqlDb = new SQL.Database();
    console.log(`[DB] Đã tạo database mới: ${dbPath}`);
  }

  const db = new DatabaseWrapper(sqlDb, dbPath);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');

  // Tạo bảng
  initializeSchema(db);

  return db;
}

// ============================================================
// Tạo bảng (Schema)
// ============================================================
function initializeSchema(db) {
  // sql.js exec cần chạy từng statement riêng
  const statements = [
    `CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT DEFAULT 'employee' CHECK(role IN ('admin','employee')),
      avatar_color TEXT DEFAULT '#667eea',
      created_at TEXT DEFAULT (datetime('now','localtime'))
    )`,
    `CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT UNIQUE NOT NULL,
      company_name TEXT,
      personal_name TEXT,
      tax_code TEXT,
      address TEXT,
      representative TEXT,
      position TEXT,
      phone TEXT,
      email TEXT,
      business_type TEXT,
      notes TEXT,
      created_by INTEGER REFERENCES users(id),
      created_at TEXT DEFAULT (datetime('now','localtime')),
      updated_at TEXT DEFAULT (datetime('now','localtime'))
    )`,
    `CREATE TABLE IF NOT EXISTS records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT UNIQUE NOT NULL,
      type TEXT NOT NULL,
      customer_id INTEGER REFERENCES customers(id),
      received_date TEXT,
      deadline TEXT,
      completed_date TEXT,
      status TEXT DEFAULT 'tiep_nhan',
      assigned_to INTEGER REFERENCES users(id),
      fee_service REAL DEFAULT 0,
      fee_state REAL DEFAULT 0,
      notes TEXT,
      created_by INTEGER REFERENCES users(id),
      created_at TEXT DEFAULT (datetime('now','localtime')),
      updated_at TEXT DEFAULT (datetime('now','localtime'))
    )`,
    `CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT UNIQUE NOT NULL,
      type TEXT NOT NULL CHECK(type IN ('thu','chi')),
      category TEXT,
      amount REAL NOT NULL,
      transaction_date TEXT,
      record_id INTEGER REFERENCES records(id) ON DELETE SET NULL,
      customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
      payment_status TEXT DEFAULT 'chua_thanh_toan',
      payment_due_date TEXT,
      paid_amount REAL DEFAULT 0,
      notes TEXT,
      created_by INTEGER REFERENCES users(id),
      created_at TEXT DEFAULT (datetime('now','localtime')),
      updated_at TEXT DEFAULT (datetime('now','localtime'))
    )`,
    `CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER REFERENCES users(id),
      title TEXT,
      message TEXT,
      type TEXT DEFAULT 'info',
      is_read INTEGER DEFAULT 0,
      record_id INTEGER,
      created_at TEXT DEFAULT (datetime('now','localtime'))
    )`,
    `CREATE TABLE IF NOT EXISTS record_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
      user_id INTEGER,
      user_name TEXT,
      action TEXT,
      details TEXT,
      created_at TEXT DEFAULT (datetime('now','localtime'))
    )`
  ];

  for (const sql of statements) {
    db.exec(sql);
  }
  db._saveNow();
  console.log('[DB] Đã khởi tạo schema thành công');
}

// ============================================================
// Hàm tạo mã tự động
// ============================================================
function generateCustomerCode(db) {
  const row = db.prepare('SELECT code FROM customers ORDER BY id DESC LIMIT 1').get();
  if (!row) return 'KH-0001';
  const match = row.code.match(/KH-(\d+)/);
  if (!match) return 'KH-0001';
  return `KH-${String(parseInt(match[1], 10) + 1).padStart(4, '0')}`;
}

function generateRecordCode(db) {
  const year = new Date().getFullYear();
  const prefix = `HS-${year}-`;
  const row = db.prepare('SELECT code FROM records WHERE code LIKE ? ORDER BY id DESC LIMIT 1').get(`${prefix}%`);
  if (!row) return `${prefix}0001`;
  const match = row.code.match(/HS-\d{4}-(\d+)/);
  if (!match) return `${prefix}0001`;
  return `${prefix}${String(parseInt(match[1], 10) + 1).padStart(4, '0')}`;
}

function generateTransactionCode(db) {
  const row = db.prepare('SELECT code FROM transactions ORDER BY id DESC LIMIT 1').get();
  if (!row) return 'GD-0001';
  const match = row.code.match(/GD-(\d+)/);
  if (!match) return 'GD-0001';
  return `GD-${String(parseInt(match[1], 10) + 1).padStart(4, '0')}`;
}

// ============================================================
// Xuất module
// ============================================================
module.exports = {
  initDatabase,
  generateCustomerCode,
  generateRecordCode,
  generateTransactionCode
};

# NAC Web App — API Specification

## Base URL: `/api`

## Endpoints

### 1. Templates
```
GET /api/templates
Response: { templates: [{ name, display_name, file_count, category }] }

GET /api/templates/{template_name}/fields
Response: { fields: [{ key, label, group, type, required }] }
```

### 2. OCR (VNeID)
```
POST /api/ocr/vneid
Body: FormData { image: File, target: "ddpl" | "tv2" }
Response: { success, data: { ho_ten, ngay_sinh, so_cccd, gioi_tinh, dia_chi_so_nha, dia_chi_xa_phuong, dia_chi_quan_huyen, dia_chi_tinh_thanh } }
```

### 3. MST Lookup
```
GET /api/mst/{mst_number}
Response: { success, data: { name, address, international_name, short_name, status } }
```

### 4. Industry Code Search
```
GET /api/nganh/search?q={query}
Response: { results: [{ ma, ten }] }
```

### 5. Document Generation
```
POST /api/documents/generate
Body: { template_name: string, data: {KEY: VALUE}, ma_nganh: [{ma, ten, is_main}] }
Response: ZIP file download
```

### 6. Service Inquiry (Upsell)
```
POST /api/services/inquiry
Body: { name, phone, email, service_type, company_name, message }
Response: { success, message }
```

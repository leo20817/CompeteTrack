# Data Model Specification

## Tables (8 total)

### 1. users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'owner',
    brand_limit INTEGER NOT NULL DEFAULT 999,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2. brands
```sql
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    brand_type TEXT NOT NULL DEFAULT 'competitor',
    google_place_id TEXT,
    website_url TEXT,
    foody_url TEXT,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_brands_user_id ON brands(user_id);
CREATE INDEX idx_brands_is_active ON brands(is_active);
```

### 3. menu_snapshots
```sql
CREATE TABLE menu_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    source TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    item_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_menu_snapshots_brand_date ON menu_snapshots(brand_id, snapshot_date DESC);
```

### 4. menu_items
```sql
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES menu_snapshots(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    category TEXT,
    price DECIMAL(12,0),
    currency TEXT NOT NULL DEFAULT 'VND',
    description TEXT,
    is_available BOOLEAN NOT NULL DEFAULT true,
    detected_at DATE NOT NULL
);
CREATE INDEX idx_menu_items_brand_id ON menu_items(brand_id);
CREATE INDEX idx_menu_items_snapshot_id ON menu_items(snapshot_id);
```

### 5. brand_changes
```sql
CREATE TABLE brand_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    field_changed TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB NOT NULL,
    ai_summary TEXT,
    old_snapshot_id UUID REFERENCES menu_snapshots(id),
    new_snapshot_id UUID REFERENCES menu_snapshots(id),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified_at TIMESTAMPTZ
);
CREATE INDEX idx_brand_changes_brand_id ON brand_changes(brand_id);
CREATE INDEX idx_brand_changes_detected_at ON brand_changes(detected_at DESC);
CREATE INDEX idx_brand_changes_notified_at ON brand_changes(notified_at) WHERE notified_at IS NULL;
CREATE INDEX idx_brand_changes_severity ON brand_changes(severity);
```

### 6. hours_snapshots
```sql
CREATE TABLE hours_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    hours_data JSONB NOT NULL,
    popular_times JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hours_snapshots_brand_date ON hours_snapshots(brand_id, snapshot_date DESC);
```

### 7. notifications
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    change_ids UUID[] NOT NULL,
    channel TEXT NOT NULL DEFAULT 'email',
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    subject TEXT,
    error_msg TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status) WHERE status = 'pending';
```

### 8. social_snapshots
```sql
CREATE TABLE social_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    followers INTEGER,
    following INTEGER,
    total_posts INTEGER,
    metrics JSONB NOT NULL,
    top_posts JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_social_snapshots_brand_platform ON social_snapshots(brand_id, platform, snapshot_date DESC);
```

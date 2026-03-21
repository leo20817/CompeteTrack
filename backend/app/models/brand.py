from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, ForeignKey, Index, Numeric,
    DateTime, text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, FullTimestampMixin


class User(FullTimestampMixin, Base):
    __tablename__ = "users"

    email = Column(Text, nullable=False, unique=True)
    plan = Column(Text, nullable=False, default="owner")
    brand_limit = Column(Integer, nullable=False, default=999)
    is_active = Column(Boolean, nullable=False, default=True)

    brands = relationship("Brand", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Brand(FullTimestampMixin, Base):
    __tablename__ = "brands"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    aliases = Column(ARRAY(Text), nullable=False, default=list)
    brand_type = Column(Text, nullable=False, default="competitor")
    google_place_id = Column(Text)
    website_url = Column(Text)
    foody_url = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="brands")
    menu_snapshots = relationship("MenuSnapshot", back_populates="brand", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="brand", cascade="all, delete-orphan")
    brand_changes = relationship("BrandChange", back_populates="brand", cascade="all, delete-orphan")
    hours_snapshots = relationship("HoursSnapshot", back_populates="brand", cascade="all, delete-orphan")
    social_snapshots = relationship("SocialSnapshot", back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_brands_user_id", "user_id"),
        Index("idx_brands_is_active", "is_active"),
    )


class MenuSnapshot(TimestampMixin, Base):
    __tablename__ = "menu_snapshots"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    source = Column(Text, nullable=False)
    raw_data = Column(JSONB, nullable=False)
    item_count = Column(Integer)

    brand = relationship("Brand", back_populates="menu_snapshots")
    menu_items = relationship("MenuItem", back_populates="snapshot", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_menu_snapshots_brand_date", "brand_id", snapshot_date.desc()),
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("menu_snapshots.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(Text, nullable=False)
    category = Column(Text)
    price = Column(Numeric(12, 0))
    currency = Column(Text, nullable=False, default="VND")
    description = Column(Text)
    is_available = Column(Boolean, nullable=False, default=True)
    detected_at = Column(Date, nullable=False)

    brand = relationship("Brand", back_populates="menu_items")
    snapshot = relationship("MenuSnapshot", back_populates="menu_items")

    __table_args__ = (
        Index("idx_menu_items_brand_id", "brand_id"),
        Index("idx_menu_items_snapshot_id", "snapshot_id"),
    )


class BrandChange(Base):
    __tablename__ = "brand_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(Text, nullable=False)
    severity = Column(Text, nullable=False)
    field_changed = Column(Text, nullable=False)
    old_value = Column(JSONB)
    new_value = Column(JSONB, nullable=False)
    ai_summary = Column(Text)
    old_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("menu_snapshots.id"))
    new_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("menu_snapshots.id"))
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    notified_at = Column(DateTime(timezone=True))

    brand = relationship("Brand", back_populates="brand_changes")

    __table_args__ = (
        Index("idx_brand_changes_brand_id", "brand_id"),
        Index("idx_brand_changes_detected_at", detected_at.desc()),
        Index("idx_brand_changes_notified_at", "notified_at", postgresql_where=notified_at.is_(None)),
        Index("idx_brand_changes_severity", "severity"),
    )


class HoursSnapshot(TimestampMixin, Base):
    __tablename__ = "hours_snapshots"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    hours_data = Column(JSONB, nullable=False)
    popular_times = Column(JSONB)

    brand = relationship("Brand", back_populates="hours_snapshots")

    __table_args__ = (
        Index("idx_hours_snapshots_brand_date", "brand_id", snapshot_date.desc()),
    )


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    change_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    channel = Column(Text, nullable=False, default="email")
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    subject = Column(Text)
    error_msg = Column(Text)
    sent_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_status", "status", postgresql_where=Column("status") == "pending"),
    )


class SocialSnapshot(TimestampMixin, Base):
    __tablename__ = "social_snapshots"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Text, nullable=False)
    snapshot_date = Column(Date, nullable=False)
    followers = Column(Integer)
    following = Column(Integer)
    total_posts = Column(Integer)
    metrics = Column(JSONB, nullable=False)
    top_posts = Column(JSONB)

    brand = relationship("Brand", back_populates="social_snapshots")

    __table_args__ = (
        Index("idx_social_snapshots_brand_platform", "brand_id", "platform", snapshot_date.desc()),
    )

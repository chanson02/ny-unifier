# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.0].define(version: 2023_06_13_161019) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "active_storage_attachments", force: :cascade do |t|
    t.string "name", null: false
    t.string "record_type", null: false
    t.bigint "record_id", null: false
    t.bigint "blob_id", null: false
    t.datetime "created_at", null: false
    t.index ["blob_id"], name: "index_active_storage_attachments_on_blob_id"
    t.index ["record_type", "record_id", "name", "blob_id"], name: "index_active_storage_attachments_uniqueness", unique: true
  end

  create_table "active_storage_blobs", force: :cascade do |t|
    t.string "key", null: false
    t.string "filename", null: false
    t.string "content_type"
    t.text "metadata"
    t.string "service_name", null: false
    t.bigint "byte_size", null: false
    t.string "checksum"
    t.datetime "created_at", null: false
    t.index ["key"], name: "index_active_storage_blobs_on_key", unique: true
  end

  create_table "active_storage_variant_records", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.string "variation_digest", null: false
    t.index ["blob_id", "variation_digest"], name: "index_active_storage_variant_records_uniqueness", unique: true
  end

  create_table "brands", force: :cascade do |t|
    t.bigint "retailer_id", null: false
    t.string "name"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["retailer_id"], name: "index_brands_on_retailer_id"
  end

  create_table "distributions", force: :cascade do |t|
    t.bigint "report_id", null: false
    t.bigint "retailer_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.bigint "brand_id"
    t.index ["brand_id"], name: "index_distributions_on_brand_id"
    t.index ["report_id"], name: "index_distributions_on_report_id"
    t.index ["retailer_id"], name: "index_distributions_on_retailer_id"
  end

  create_table "headers", force: :cascade do |t|
    t.string "value"
    t.bigint "instruction_id"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["instruction_id"], name: "index_headers_on_instruction_id"
  end

  create_table "instructions", force: :cascade do |t|
    t.string "structure"
    t.integer "retailer"
    t.text "brand"
    t.text "address"
    t.integer "phone"
    t.integer "website"
    t.integer "premise"
    t.string "chain"
    t.string "condition"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "reports", force: :cascade do |t|
    t.string "name"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.bigint "header_id"
    t.integer "head_row"
    t.string "selected_blob"
    t.boolean "parsed", default: false
    t.index ["header_id"], name: "index_reports_on_header_id"
  end

  create_table "retailers", force: :cascade do |t|
    t.string "name", null: false
    t.string "adr_hash"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "slug", null: false
    t.string "street"
    t.string "city"
    t.string "state"
    t.string "postal"
    t.string "country"
  end

  add_foreign_key "active_storage_attachments", "active_storage_blobs", column: "blob_id"
  add_foreign_key "active_storage_variant_records", "active_storage_blobs", column: "blob_id"
  add_foreign_key "brands", "retailers"
  add_foreign_key "distributions", "brands"
  add_foreign_key "distributions", "reports"
  add_foreign_key "distributions", "retailers"
  add_foreign_key "headers", "instructions"
  add_foreign_key "reports", "headers"
end

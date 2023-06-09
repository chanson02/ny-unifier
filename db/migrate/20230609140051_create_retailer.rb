class CreateRetailer < ActiveRecord::Migration[7.0]
  def change
    create_table :retailers do |t|
      t.string :name
      t.string :adr_hash, null: true

      t.timestamps
    end
  end
end

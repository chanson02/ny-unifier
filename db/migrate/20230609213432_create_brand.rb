class CreateBrand < ActiveRecord::Migration[7.0]
  def change
    create_table :brands do |t|
      t.references :retailer, null: false, foreign_key: true
      t.string :name

      t.timestamps
    end
  end
end

class CreateInstructions < ActiveRecord::Migration[7.0]
  def change
    create_table :instructions do |t|
      t.string :structure
      t.integer :account
      t.text :brand
      t.text :address
      t.integer :phone
      t.integer :website
      t.integer :premise
      t.string :chain
      t.string :condition

      t.timestamps
    end
  end
end

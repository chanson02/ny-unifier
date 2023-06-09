class CreateRetailers < ActiveRecord::Migration[7.0]
  def change
    create_table :retailers do |t|
      t.string :name
      t.string :hash
      t.string :full_location
      t.string :street1
      t.string :street2
      t.string :city
      t.string :state
      t.string :postal

      t.timestamps
    end
  end
end


class AddRawValuesToDistributions < ActiveRecord::Migration[7.0]
  def change
    add_column :distributions, :address, :string, null: true
    add_column :distributions, :brands, :string, null: true
  end
end

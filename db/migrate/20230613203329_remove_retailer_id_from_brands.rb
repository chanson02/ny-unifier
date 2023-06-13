class RemoveRetailerIdFromBrands < ActiveRecord::Migration[7.0]
  def change
    remove_column :brands, :retailer_id
  end
end

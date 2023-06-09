class RenameAccountToRetailerInstructions < ActiveRecord::Migration[7.0]
  def change
    rename_column :instructions, :account, :retailer
  end
end

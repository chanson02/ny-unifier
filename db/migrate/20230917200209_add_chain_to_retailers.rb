class AddChainToRetailers < ActiveRecord::Migration[7.0]
  def change
    add_column :retailers, :chain_id, :integer
  end
end

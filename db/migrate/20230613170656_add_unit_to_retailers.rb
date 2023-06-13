class AddUnitToRetailers < ActiveRecord::Migration[7.0]
  def change
    add_column :retailers, :unit, :string, null: true, after: :street
  end
end

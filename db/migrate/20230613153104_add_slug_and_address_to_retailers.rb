class AddSlugAndAddressToRetailers < ActiveRecord::Migration[7.0]
  def change
    add_column :retailers, :slug, :string, null: false
    add_column :retailers, :street, :string
    add_column :retailers, :city, :string
    add_column :retailers, :state, :string
    add_column :retailers, :postal, :string
    add_column :retailers, :country, :string

    change_column_null :retailers, :name, false
  end
end

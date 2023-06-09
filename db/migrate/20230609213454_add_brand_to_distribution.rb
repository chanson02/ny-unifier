class AddBrandToDistribution < ActiveRecord::Migration[7.0]
  def change
    add_reference :distributions, :brand, null: true, foreign_key: true
  end
end

class CreateDistribution < ActiveRecord::Migration[7.0]
  def change
    create_table :distributions do |t|
      t.references :report, null: false, foreign_key: true
      t.references :retailer, null: false, foreign_key: true

      t.timestamps
    end
  end
end

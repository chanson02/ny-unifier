class CreateContainers < ActiveRecord::Migration[7.0]
  def change
    create_table :containers do |t|
      t.string :name
      t.date :date

      t.timestamps
    end
  end
end

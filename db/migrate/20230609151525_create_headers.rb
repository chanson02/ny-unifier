class CreateHeaders < ActiveRecord::Migration[7.0]
  def change
    create_table :headers do |t|
      t.string :value
      t.references :instruction, null: false, foreign_key: true

      t.timestamps
    end
  end
end

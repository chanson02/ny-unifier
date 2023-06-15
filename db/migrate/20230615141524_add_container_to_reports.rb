class AddContainerToReports < ActiveRecord::Migration[7.0]
  def change
    add_reference :reports, :container, null: false, foreign_key: true
  end
end

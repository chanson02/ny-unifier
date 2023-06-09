class UpdateInstructionReferenceNullInHeader < ActiveRecord::Migration[7.0]
  def change
    change_column_null :headers, :instruction_id, true
  end
end

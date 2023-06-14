# frozen_string_literal: true

# Instructions controller
class InstructionsController < ApplicationController
  def new
    @reports = Report.all
    @report = Report.find(params[:report_id]) if params[:report_id]
    @instruction = Instruction.new
  end

  def create
    @instruction = Instruction.from_params(params)
    if @instruction&.save
      h = Header.find(params[:instruction][:header_id])
      h.instruction_id = @instruction.id
      h.save
      redirect_to reports_path, notice: 'Instruction saved'
    else
      render :new
    end
  end

  private

  def allowed_params
    params.require(:instruction)
  end
end

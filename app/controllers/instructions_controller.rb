# frozen_string_literal: true

# Instructions controller
class InstructionsController < ApplicationController
  def new
    @reports = Report.all
    @instruction = Instruction.new
  end

  def create
    @instruction = Instruction.from_params(params)
    if @instruction&.save
      redirect_to reports_path, notice: 'Instruction saved'
    else
      render :new
    end
  end

  private

  def allowed_params
    params.require(:instruction).permit(:header, :structure, :retailer, :brand, :street1, :street2, :city, :state, :postal, :country, :website, :phone, :premise, :chain, :condition)
  end
end

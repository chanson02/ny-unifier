# frozen_string_literal: true

# Retailers controller
class RetailersController < ApplicationController
  def edit
    @retailer = Retailer.find(params[:id])
  end

  def update
    @retailer = Retailer.find(params[:id])
    if @retailer.update(allowed_params)
      redirect_to retailer_path(@retailer), notice: 'Retailer updated successfully'
    else
      render :edit
    end
  end

  private

  def allowed_params
    params.require(:retailer).permit(:street, :city, :state, :postal, :country)
  end
end

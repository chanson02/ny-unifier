# frozen_string_literal: true

# Containers controller
class ContainersController < ApplicationController
  def index
    @containers = Container.all
  end

  def show
    @container = Container.find(params[:id])
  end

  def new
    @container = Container.new
  end

  def create
    @container = Container.new(allowed_params)
    @container.save ? redirect_to(containers_path) : render(:new)
  end

  def update
    @container = Container.find(params[:id])
    render :show
  end

  private

  def allowed_params
    params.require(:container).permit(:name, :date)
  end
end

# frozen_string_literal: true

Rails.application.routes.draw do
  resources :reports
  resources :retailers, only: %i[edit update]
  resources :instructions, only: %i[new create]
  root 'reports#index'
end

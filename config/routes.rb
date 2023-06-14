# frozen_string_literal: true

Rails.application.routes.draw do
  resources :reports
  get '/reports/:id/unifier-report', to: 'reports#unifier_report', as: 'unifier_report'
  get '/reports/:id/head', to: 'reports#select_head', as: 'select_head'
  patch '/reports/:id/head', to: 'reports#save_head', as: 'save_head'

  resources :retailers, only: %i[edit update]
  resources :instructions, only: %i[new create]
  root 'reports#index'
end

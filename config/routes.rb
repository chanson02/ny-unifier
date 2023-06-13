Rails.application.routes.draw do
  resources :reports
  resources :retailers, only: [:edit, :update]
  resources :instructions, only: [:new, :create]
  # root "articles#index"
end

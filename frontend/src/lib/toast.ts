// Simple toast utility for notifications
// In a real application, you might want to use a library like react-hot-toast or react-toastify

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  duration?: number
  type?: ToastType
}

class ToastManager {
  private createToast(message: string, type: ToastType = 'info', duration: number = 5000) {
    // Create toast element
    const toast = document.createElement('div')
    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full ${
      type === 'success' ? 'bg-green-500 text-white' :
      type === 'error' ? 'bg-red-500 text-white' :
      type === 'warning' ? 'bg-yellow-500 text-black' :
      'bg-blue-500 text-white'
    }`
    
    toast.innerHTML = `
      <div class="flex items-center">
        <span class="mr-2">
          ${type === 'success' ? '✅' : 
            type === 'error' ? '❌' : 
            type === 'warning' ? '⚠️' : 'ℹ️'}
        </span>
        <span>${message}</span>
        <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
          ✕
        </button>
      </div>
    `

    // Add to DOM
    document.body.appendChild(toast)

    // Animate in
    setTimeout(() => {
      toast.classList.remove('translate-x-full')
    }, 100)

    // Auto remove
    setTimeout(() => {
      toast.classList.add('translate-x-full')
      setTimeout(() => {
        if (toast.parentElement) {
          toast.parentElement.removeChild(toast)
        }
      }, 300)
    }, duration)
  }

  success(message: string, options?: ToastOptions) {
    this.createToast(message, 'success', options?.duration)
  }

  error(message: string, options?: ToastOptions) {
    this.createToast(message, 'error', options?.duration)
  }

  warning(message: string, options?: ToastOptions) {
    this.createToast(message, 'warning', options?.duration)
  }

  info(message: string, options?: ToastOptions) {
    this.createToast(message, 'info', options?.duration)
  }
}

export const toast = new ToastManager()

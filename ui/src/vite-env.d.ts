/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_GATEWAY: string;
  readonly VITE_API_CART: string;
  readonly VITE_API_CATALOG: string;
  readonly VITE_API_SEARCH: string;
  readonly VITE_API_PAYMENT: string;
  readonly VITE_API_NOTIFICATION: string;
  readonly VITE_API_SELLER: string;
  readonly VITE_API_ADMIN: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

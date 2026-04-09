const DB_NAME = "rajeshgpt-browser-cache";
const DB_VERSION = 1;
const DOCUMENT_STORE = "documents";

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(DOCUMENT_STORE)) {
        db.createObjectStore(DOCUMENT_STORE, { keyPath: "id" });
      }
    };
  });
}

async function withStore(mode, callback) {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(DOCUMENT_STORE, mode);
    const store = transaction.objectStore(DOCUMENT_STORE);

    let result;
    transaction.oncomplete = () => {
      db.close();
      resolve(result);
    };
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };

    result = callback(store);
  });
}

export async function listCachedDocuments() {
  return withStore("readonly", (store) => {
    const request = store.getAll();
    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        const documents = request.result || [];
        documents.sort((left, right) => {
          return new Date(right.uploadedAt || 0).getTime() - new Date(left.uploadedAt || 0).getTime();
        });
        resolve(documents);
      };
      request.onerror = () => reject(request.error);
    });
  });
}

export async function getCachedDocumentsByIds(ids) {
  const requestedIds = Array.from(new Set(ids || []));
  if (!requestedIds.length) {
    return [];
  }

  return withStore("readonly", (store) => {
    const reads = requestedIds.map(
      (id) =>
        new Promise((resolve, reject) => {
          const request = store.get(id);
          request.onsuccess = () => resolve(request.result || null);
          request.onerror = () => reject(request.error);
        }),
    );

    return Promise.all(reads).then((documents) => documents.filter(Boolean));
  });
}

export async function saveCachedDocument(document) {
  return withStore("readwrite", (store) => {
    const request = store.put(document);
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(document);
      request.onerror = () => reject(request.error);
    });
  });
}

export async function deleteCachedDocument(id) {
  return withStore("readwrite", (store) => {
    const request = store.delete(id);
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(request.error);
    });
  });
}

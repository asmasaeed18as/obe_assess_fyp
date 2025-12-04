// // src/api/axios.js
// import axios from "axios";

// const API_BASE = "http://localhost:8000/api";

// const api = axios.create({
//   baseURL: API_BASE,
//   headers: {
//     "Content-Type": "application/json",
//   },
// });

// let isRefreshing = false;
// let failedQueue = [];

// const processQueue = (error, token = null) => {
//   failedQueue.forEach(prom => {
//     if (error) {
//       prom.reject(error);
//     } else {
//       prom.resolve(token);
//     }
//   });
//   failedQueue = [];
// };

// api.interceptors.request.use((config) => {
//   const access = localStorage.getItem("access_token");
//   if (access) {
//     config.headers["Authorization"] = `Bearer ${access}`;
//   }
//   return config;
// });

// api.interceptors.response.use(
//   (res) => res,
//   (err) => {
//     const originalRequest = err.config;
//     if (err.response && err.response.status === 401 && !originalRequest._retry) {
//       // try refresh
//       if (isRefreshing) {
//         return new Promise(function (resolve, reject) {
//           failedQueue.push({ resolve, reject });
//         })
//           .then(token => {
//             originalRequest.headers['Authorization'] = 'Bearer ' + token;
//             return axios(originalRequest);
//           })
//           .catch(err => Promise.reject(err));
//       }

//       originalRequest._retry = true;
//       isRefreshing = true;

//       const refreshToken = localStorage.getItem("refresh_token");
//       if (!refreshToken) {
//         isRefreshing = false;
//         return Promise.reject(err);
//       }

//       return new Promise(function (resolve, reject) {
//         axios.post(`${API_BASE}/users/token/refresh/`, { refresh: refreshToken })
//           .then(({ data }) => {
//             localStorage.setItem("access_token", data.access);
//             api.defaults.headers['Authorization'] = 'Bearer ' + data.access;
//             processQueue(null, data.access);
//             resolve(api(originalRequest));
//           })
//           .catch((error) => {
//             processQueue(error, null);
//             reject(error);
//           })
//           .finally(() => {
//             isRefreshing = false;
//           });
//       });
//     }
//     return Promise.reject(err);
//   }
// );

// export default api;



// src/api/axios.js
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api"; // ✅ Make sure this matches Django port

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access_token");
  if (access) config.headers["Authorization"] = `Bearer ${access}`;
  return config;
});

export default api;

/**
 * API Helper for standardized response format
 *
 * All API responses follow this format:
 * {
 *   success: boolean,
 *   message: string,
 *   data: object | null
 * }
 */

const API_V1_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Handle API response
 * @param {Response} response - Fetch API response
 * @returns {Promise<object>} - Parsed response data
 */
async function handleAPIResponse(response) {
    const data = await response.json();

    if (response.ok && data.success) {
        return data;
    } else {
        throw new Error(data.message || 'API request failed');
    }
}

/**
 * API Client
 */
const API = {
    // Authentication
    auth: {
        googleConfig: async () => {
            const response = await fetch(`${API_V1_BASE_URL}/auth/google/config`);
            return handleAPIResponse(response);
        },
        googleLogin: async (accessToken) => {
            const response = await fetch(`${API_V1_BASE_URL}/auth/google/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ access_token: accessToken })
            });
            return handleAPIResponse(response);
        }
    },

    // Users
    users: {
        me: async (token) => {
            const response = await fetch(`${API_V1_BASE_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            return handleAPIResponse(response);
        },
        profile: {
            get: async (token) => {
                const response = await fetch(`${API_V1_BASE_URL}/users/me/profile`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                return handleAPIResponse(response);
            },
            create: async (token, profileData) => {
                const response = await fetch(`${API_V1_BASE_URL}/users/me/profile`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(profileData)
                });
                return handleAPIResponse(response);
            },
            update: async (token, profileData) => {
                const response = await fetch(`${API_V1_BASE_URL}/users/me/profile`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(profileData)
                });
                return handleAPIResponse(response);
            }
        }
    },

    // Master Data
    master: {
        languages: async () => {
            const response = await fetch(`${API_V1_BASE_URL}/master/languages`);
            return handleAPIResponse(response);
        },
        countries: async () => {
            const response = await fetch(`${API_V1_BASE_URL}/master/countries`);
            return handleAPIResponse(response);
        }
    }
};

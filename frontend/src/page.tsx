'use client'

import { SignInButton, SignedIn, SignedOut, UserButton, useUser } from '@clerk/nextjs'
import { useEffect, useState } from 'react'
import { apiCall } from '@/lib/api'

export default function Home() {
  const { user, isLoaded } = useUser()
  const [userData, setUserData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isLoaded && user) {
      fetchUserData()
    }
  }, [isLoaded, user])

  const fetchUserData = async () => {
    setLoading(true)
    try {
      const response = await apiCall('/api/users/me')
      const data = await response.json()
      setUserData(data)
    } catch (error) {
      console.error('Error fetching user data:', error)
    }
    setLoading(false)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Hackathon Starter</h1>
      
      <div className="flex gap-4">
        {/* Show this if user is NOT logged in */}
        <SignedOut>
          <SignInButton mode="modal">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Sign In with Google
            </button>
          </SignInButton>
        </SignedOut>

        {/* Show this if user IS logged in */}
        <SignedIn>
          <div className="flex flex-col items-center gap-4">
            <p className="text-xl">Welcome back!</p>
            <UserButton afterSignOutUrl="/" />
            
            {loading && <p>Loading backend data...</p>}
            {userData && (
              <div className="mt-4 p-4 bg-gray-100 rounded">
                <p className="font-bold">Backend Response:</p>
                <pre className="text-sm">{JSON.stringify(userData, null, 2)}</pre>
              </div>
            )}
          </div>
        </SignedIn>
      </div>
    </main>
  )
}
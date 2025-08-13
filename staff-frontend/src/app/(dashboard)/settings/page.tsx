<<<<<<< HEAD
"use client";

import React, { useState } from "react";
import { debug } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
=======
'use client'

import React, { useState } from 'react'
import { debug } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
>>>>>>> main
import {
  UserCircleIcon,
  KeyIcon,
  BellIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
  TrashIcon,
  ExclamationTriangleIcon,
<<<<<<< HEAD
} from "@heroicons/react/24/outline";

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [isLoading, setIsLoading] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    company: "",
    bio: "",
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
=======
} from '@heroicons/react/24/outline'

export default function SettingsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')
  const [isLoading, setIsLoading] = useState(false)
  
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    company: '',
    bio: '',
  })

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
>>>>>>> main

  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    weeklyReports: true,
    securityAlerts: true,
    productUpdates: false,
<<<<<<< HEAD
  });

  const [preferences, setPreferences] = useState({
    theme: "dark",
    language: "en",
    timezone: "UTC",
    dateFormat: "MM/DD/YYYY",
  });

  const tabs = [
    { id: "profile", name: "Profile", icon: UserCircleIcon },
    { id: "security", name: "Security", icon: ShieldCheckIcon },
    { id: "notifications", name: "Notifications", icon: BellIcon },
    { id: "preferences", name: "Preferences", icon: PaintBrushIcon },
    { id: "api", name: "API Keys", icon: KeyIcon },
    { id: "danger", name: "Danger Zone", icon: ExclamationTriangleIcon },
  ];

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      debug("Profile saved", profileData);
    }, 1000);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert("Passwords do not match");
      return;
    }
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
      debug("Password changed", {});
    }, 1000);
  };

  const handleSaveNotifications = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      debug("Notifications saved", notificationSettings);
    }, 1000);
  };

  const handleSavePreferences = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      debug("Preferences saved", preferences);
    }, 1000);
  };
=======
  })

  const [preferences, setPreferences] = useState({
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
  })

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserCircleIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'preferences', name: 'Preferences', icon: PaintBrushIcon },
    { id: 'api', name: 'API Keys', icon: KeyIcon },
    { id: 'danger', name: 'Danger Zone', icon: ExclamationTriangleIcon },
  ]

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
      debug('Profile saved', profileData)
    }, 1000)
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('Passwords do not match')
      return
    }
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      debug('Password changed', {})
    }, 1000)
  }

  const handleSaveNotifications = async () => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
      debug('Notifications saved', notificationSettings)
    }, 1000)
  }

  const handleSavePreferences = async () => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
      debug('Preferences saved', preferences)
    }, 1000)
  }
>>>>>>> main

  const renderProfileTab = () => (
    <div className="space-y-6">
      <div>
<<<<<<< HEAD
        <h2 className="text-xl font-semibold text-white mb-2">
          Profile Information
        </h2>
        <p className="text-gray-400">
          Update your account profile information.
        </p>
=======
        <h2 className="text-xl font-semibold text-white mb-2">Profile Information</h2>
        <p className="text-gray-400">Update your account profile information.</p>
>>>>>>> main
      </div>

      <form onSubmit={handleSaveProfile} className="space-y-6">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
            <UserCircleIcon className="h-10 w-10 text-white" />
          </div>
          <div>
            <Button variant="outline" size="sm">
              Change Avatar
            </Button>
<<<<<<< HEAD
            <p className="text-sm text-gray-400 mt-1">
              JPG, GIF or PNG. 1MB max.
            </p>
=======
            <p className="text-sm text-gray-400 mt-1">JPG, GIF or PNG. 1MB max.</p>
>>>>>>> main
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input
            label="Full Name"
            value={profileData.name}
<<<<<<< HEAD
            onChange={(value) =>
              setProfileData((prev) => ({ ...prev, name: value }))
            }
=======
            onChange={(value) => setProfileData(prev => ({ ...prev, name: value }))}
>>>>>>> main
            required
          />
          <Input
            label="Email Address"
            type="email"
            value={profileData.email}
<<<<<<< HEAD
            onChange={(value) =>
              setProfileData((prev) => ({ ...prev, email: value }))
            }
=======
            onChange={(value) => setProfileData(prev => ({ ...prev, email: value }))}
>>>>>>> main
            required
          />
        </div>

        <Input
          label="Company (Optional)"
          value={profileData.company}
<<<<<<< HEAD
          onChange={(value) =>
            setProfileData((prev) => ({ ...prev, company: value }))
          }
=======
          onChange={(value) => setProfileData(prev => ({ ...prev, company: value }))}
>>>>>>> main
        />

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Bio
          </label>
          <textarea
            value={profileData.bio}
<<<<<<< HEAD
            onChange={(e) =>
              setProfileData((prev) => ({ ...prev, bio: e.target.value }))
            }
=======
            onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
>>>>>>> main
            placeholder="Tell us about yourself..."
            className="w-full h-24 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none"
          />
        </div>

        <div className="flex justify-end">
          <Button type="submit" variant="primary" loading={isLoading}>
            Save Changes
          </Button>
        </div>
      </form>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main

  const renderSecurityTab = () => (
    <div className="space-y-6">
      <div>
<<<<<<< HEAD
        <h2 className="text-xl font-semibold text-white mb-2">
          Security Settings
        </h2>
        <p className="text-gray-400">
          Manage your account security and authentication.
        </p>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Change Password
        </h3>
=======
        <h2 className="text-xl font-semibold text-white mb-2">Security Settings</h2>
        <p className="text-gray-400">Manage your account security and authentication.</p>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Change Password</h3>
>>>>>>> main
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            value={passwordData.currentPassword}
<<<<<<< HEAD
            onChange={(value) =>
              setPasswordData((prev) => ({ ...prev, currentPassword: value }))
            }
=======
            onChange={(value) => setPasswordData(prev => ({ ...prev, currentPassword: value }))}
>>>>>>> main
            required
          />
          <Input
            label="New Password"
            type="password"
            value={passwordData.newPassword}
<<<<<<< HEAD
            onChange={(value) =>
              setPasswordData((prev) => ({ ...prev, newPassword: value }))
            }
=======
            onChange={(value) => setPasswordData(prev => ({ ...prev, newPassword: value }))}
>>>>>>> main
            required
          />
          <Input
            label="Confirm New Password"
            type="password"
            value={passwordData.confirmPassword}
<<<<<<< HEAD
            onChange={(value) =>
              setPasswordData((prev) => ({ ...prev, confirmPassword: value }))
            }
=======
            onChange={(value) => setPasswordData(prev => ({ ...prev, confirmPassword: value }))}
>>>>>>> main
            required
          />
          <div className="flex justify-end">
            <Button type="submit" variant="primary" loading={isLoading}>
              Update Password
            </Button>
          </div>
        </form>
      </Card>

      <Card className="p-6">
<<<<<<< HEAD
        <h3 className="text-lg font-semibold text-white mb-4">
          Two-Factor Authentication
        </h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-300">
              Add an extra layer of security to your account
            </p>
            <p className="text-sm text-gray-400">Status: Not enabled</p>
          </div>
          <Button variant="outline">Enable 2FA</Button>
=======
        <h3 className="text-lg font-semibold text-white mb-4">Two-Factor Authentication</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-300">Add an extra layer of security to your account</p>
            <p className="text-sm text-gray-400">Status: Not enabled</p>
          </div>
          <Button variant="outline">
            Enable 2FA
          </Button>
>>>>>>> main
        </div>
      </Card>

      <Card className="p-6">
<<<<<<< HEAD
        <h3 className="text-lg font-semibold text-white mb-4">
          Active Sessions
        </h3>
=======
        <h3 className="text-lg font-semibold text-white mb-4">Active Sessions</h3>
>>>>>>> main
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <div>
              <p className="text-white">Current Session</p>
<<<<<<< HEAD
              <p className="text-sm text-gray-400">
                Chrome on macOS • San Francisco, CA
              </p>
            </div>
            <span className="bg-green-500/10 text-green-400 px-2 py-1 rounded text-xs">
              Current
            </span>
=======
              <p className="text-sm text-gray-400">Chrome on macOS • San Francisco, CA</p>
            </div>
            <span className="bg-green-500/10 text-green-400 px-2 py-1 rounded text-xs">Current</span>
>>>>>>> main
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <div>
              <p className="text-white">Mobile App</p>
              <p className="text-sm text-gray-400">iPhone • 2 hours ago</p>
            </div>
            <Button variant="outline" size="sm">
              Revoke
            </Button>
          </div>
        </div>
      </Card>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main

  const renderNotificationsTab = () => (
    <div className="space-y-6">
      <div>
<<<<<<< HEAD
        <h2 className="text-xl font-semibold text-white mb-2">
          Notification Preferences
        </h2>
        <p className="text-gray-400">
          Choose how you want to be notified about account activity.
        </p>
=======
        <h2 className="text-xl font-semibold text-white mb-2">Notification Preferences</h2>
        <p className="text-gray-400">Choose how you want to be notified about account activity.</p>
>>>>>>> main
      </div>

      <Card className="p-6">
        <div className="space-y-6">
          {Object.entries(notificationSettings).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <h4 className="text-white font-medium">
<<<<<<< HEAD
                  {key
                    .replace(/([A-Z])/g, " $1")
                    .replace(/^./, (str) => str.toUpperCase())}
                </h4>
                <p className="text-sm text-gray-400">
                  {key === "emailNotifications" &&
                    "Receive notifications via email"}
                  {key === "pushNotifications" &&
                    "Receive push notifications in your browser"}
                  {key === "weeklyReports" &&
                    "Get weekly usage and activity reports"}
                  {key === "securityAlerts" &&
                    "Important security-related notifications"}
                  {key === "productUpdates" &&
                    "News about new features and updates"}
                </p>
              </div>
              <button
                onClick={() =>
                  setNotificationSettings((prev) => ({
                    ...prev,
                    [key]: !value,
                  }))
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  value ? "bg-orange-500" : "bg-slate-600"
=======
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </h4>
                <p className="text-sm text-gray-400">
                  {key === 'emailNotifications' && 'Receive notifications via email'}
                  {key === 'pushNotifications' && 'Receive push notifications in your browser'}
                  {key === 'weeklyReports' && 'Get weekly usage and activity reports'}
                  {key === 'securityAlerts' && 'Important security-related notifications'}
                  {key === 'productUpdates' && 'News about new features and updates'}
                </p>
              </div>
              <button
                onClick={() => setNotificationSettings(prev => ({ ...prev, [key]: !value }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  value ? 'bg-orange-500' : 'bg-slate-600'
>>>>>>> main
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
<<<<<<< HEAD
                    value ? "translate-x-6" : "translate-x-1"
=======
                    value ? 'translate-x-6' : 'translate-x-1'
>>>>>>> main
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
<<<<<<< HEAD

        <div className="pt-6 border-t border-slate-600">
          <Button
            variant="primary"
            onClick={handleSaveNotifications}
            loading={isLoading}
          >
=======
        
        <div className="pt-6 border-t border-slate-600">
          <Button variant="primary" onClick={handleSaveNotifications} loading={isLoading}>
>>>>>>> main
            Save Preferences
          </Button>
        </div>
      </Card>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      <div>
<<<<<<< HEAD
        <h2 className="text-xl font-semibold text-white mb-2">
          Application Preferences
        </h2>
=======
        <h2 className="text-xl font-semibold text-white mb-2">Application Preferences</h2>
>>>>>>> main
        <p className="text-gray-400">Customize your application experience.</p>
      </div>

      <Card className="p-6">
        <div className="space-y-6">
          <div>
<<<<<<< HEAD
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Theme
            </label>
            <select
              value={preferences.theme}
              onChange={(e) =>
                setPreferences((prev) => ({ ...prev, theme: e.target.value }))
              }
=======
            <label className="block text-sm font-medium text-gray-300 mb-2">Theme</label>
            <select
              value={preferences.theme}
              onChange={(e) => setPreferences(prev => ({ ...prev, theme: e.target.value }))}
>>>>>>> main
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="auto">Auto</option>
            </select>
          </div>

          <div>
<<<<<<< HEAD
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Language
            </label>
            <select
              value={preferences.language}
              onChange={(e) =>
                setPreferences((prev) => ({
                  ...prev,
                  language: e.target.value,
                }))
              }
=======
            <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
            <select
              value={preferences.language}
              onChange={(e) => setPreferences(prev => ({ ...prev, language: e.target.value }))}
>>>>>>> main
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>

          <div>
<<<<<<< HEAD
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Timezone
            </label>
            <select
              value={preferences.timezone}
              onChange={(e) =>
                setPreferences((prev) => ({
                  ...prev,
                  timezone: e.target.value,
                }))
              }
=======
            <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
            <select
              value={preferences.timezone}
              onChange={(e) => setPreferences(prev => ({ ...prev, timezone: e.target.value }))}
>>>>>>> main
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
            </select>
          </div>

          <div>
<<<<<<< HEAD
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Date Format
            </label>
            <select
              value={preferences.dateFormat}
              onChange={(e) =>
                setPreferences((prev) => ({
                  ...prev,
                  dateFormat: e.target.value,
                }))
              }
=======
            <label className="block text-sm font-medium text-gray-300 mb-2">Date Format</label>
            <select
              value={preferences.dateFormat}
              onChange={(e) => setPreferences(prev => ({ ...prev, dateFormat: e.target.value }))}
>>>>>>> main
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-600">
<<<<<<< HEAD
          <Button
            variant="primary"
            onClick={handleSavePreferences}
            loading={isLoading}
          >
=======
          <Button variant="primary" onClick={handleSavePreferences} loading={isLoading}>
>>>>>>> main
            Save Preferences
          </Button>
        </div>
      </Card>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main

  const renderAPITab = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibent text-white mb-2">API Keys</h2>
<<<<<<< HEAD
        <p className="text-gray-400">
          Manage your API keys for programmatic access.
        </p>
=======
        <p className="text-gray-400">Manage your API keys for programmatic access.</p>
>>>>>>> main
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Your API Keys</h3>
          <Button variant="primary">
            <KeyIcon className="h-4 w-4 mr-2" />
            Generate New Key
          </Button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
            <div>
              <p className="text-white font-medium">Production Key</p>
<<<<<<< HEAD
              <p className="text-sm text-gray-400 font-mono">
                sk_prod_••••••••••••••••••••••••••••••••
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Created on Jan 15, 2024 • Last used 2 hours ago
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                Copy
              </Button>
              <Button variant="outline" size="sm">
                Regenerate
              </Button>
              <Button variant="outline" size="sm">
                Delete
              </Button>
=======
              <p className="text-sm text-gray-400 font-mono">sk_prod_••••••••••••••••••••••••••••••••</p>
              <p className="text-xs text-gray-500 mt-1">Created on Jan 15, 2024 • Last used 2 hours ago</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">Copy</Button>
              <Button variant="outline" size="sm">Regenerate</Button>
              <Button variant="outline" size="sm">Delete</Button>
>>>>>>> main
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
            <div>
              <p className="text-white font-medium">Development Key</p>
<<<<<<< HEAD
              <p className="text-sm text-gray-400 font-mono">
                sk_dev_••••••••••••••••••••••••••••••••
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Created on Jan 10, 2024 • Last used 1 day ago
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                Copy
              </Button>
              <Button variant="outline" size="sm">
                Regenerate
              </Button>
              <Button variant="outline" size="sm">
                Delete
              </Button>
=======
              <p className="text-sm text-gray-400 font-mono">sk_dev_••••••••••••••••••••••••••••••••</p>
              <p className="text-xs text-gray-500 mt-1">Created on Jan 10, 2024 • Last used 1 day ago</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">Copy</Button>
              <Button variant="outline" size="sm">Regenerate</Button>
              <Button variant="outline" size="sm">Delete</Button>
>>>>>>> main
            </div>
          </div>
        </div>
      </Card>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main

  const renderDangerTab = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-2">Danger Zone</h2>
        <p className="text-gray-400">Irreversible and destructive actions.</p>
      </div>

      <Card className="p-6 border-red-500/20">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
          Delete Account
        </h3>
        <p className="text-gray-400 mb-4">
<<<<<<< HEAD
          Once you delete your account, there is no going back. Please be
          certain. This action will:
=======
          Once you delete your account, there is no going back. Please be certain.
          This action will:
>>>>>>> main
        </p>
        <ul className="text-sm text-gray-400 mb-6 space-y-1 ml-4">
          <li>• Delete all your projects and code</li>
          <li>• Cancel your subscription</li>
          <li>• Remove all API keys</li>
          <li>• Delete all support tickets</li>
        </ul>
<<<<<<< HEAD
        <Button
          variant="outline"
          className="border-red-500 text-red-400 hover:bg-red-500/10"
        >
=======
        <Button variant="outline" className="border-red-500 text-red-400 hover:bg-red-500/10">
>>>>>>> main
          <TrashIcon className="h-4 w-4 mr-2" />
          Delete Account
        </Button>
      </Card>
    </div>
<<<<<<< HEAD
  );

  const tabContentMap: Record<string, () => React.JSX.Element> = {
=======
  )

  const tabContentMap: Record<string, () => JSX.Element> = {
>>>>>>> main
    profile: renderProfileTab,
    security: renderSecurityTab,
    notifications: renderNotificationsTab,
    preferences: renderPreferencesTab,
    api: renderAPITab,
    danger: renderDangerTab,
<<<<<<< HEAD
  };

  const renderTabContent = () => {
    return tabContentMap[activeTab]?.() ?? renderProfileTab();
  };
=======
  }

  const renderTabContent = () => {
    return tabContentMap[activeTab]?.() ?? renderProfileTab()
  }
>>>>>>> main

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
<<<<<<< HEAD
        <p className="text-gray-400">
          Manage your account settings and preferences
        </p>
=======
        <p className="text-gray-400">Manage your account settings and preferences</p>
>>>>>>> main
      </div>

      <div className="lg:grid lg:grid-cols-4 lg:gap-8">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => {
<<<<<<< HEAD
              const Icon = tab.icon;
=======
              const Icon = tab.icon
>>>>>>> main
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
<<<<<<< HEAD
                      ? "bg-orange-500/10 text-orange-400 border-r-2 border-orange-500"
                      : "text-gray-300 hover:bg-slate-700 hover:text-white"
=======
                      ? 'bg-orange-500/10 text-orange-400 border-r-2 border-orange-500'
                      : 'text-gray-300 hover:bg-slate-700 hover:text-white'
>>>>>>> main
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {tab.name}
                </button>
<<<<<<< HEAD
              );
=======
              )
>>>>>>> main
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="mt-6 lg:mt-0 lg:col-span-3">
<<<<<<< HEAD
          <Card className="p-6">{renderTabContent()}</Card>
        </div>
      </div>
    </div>
  );
}
=======
          <Card className="p-6">
            {renderTabContent()}
          </Card>
        </div>
      </div>
    </div>
  )
}
>>>>>>> main

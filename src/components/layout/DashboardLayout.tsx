import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  CheckCircle2, 
  Coins, 
  Settings, 
  LogOut, 
  ShieldCheck,
  Menu,
  X,
  Wallet
} from 'lucide-react';
import { Button } from '../ui/button';
import { useAuth } from '../../hooks/useAuth';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../ui/dropdown-menu';
import { cn } from '../../lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Upload', href: '/upload', icon: Upload },
  { name: 'Verifications', href: '/verifications', icon: CheckCircle2 },
  { name: 'Rewards', href: '/rewards', icon: Coins },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 flex-col bg-sidebar border-r border-border shadow-xl z-20">
        <div className="h-16 flex items-center px-6 border-b border-border/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-[0_0_15px_rgba(0,245,212,0.4)]">
              <ShieldCheck className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-xl tracking-tight">NWU <span className="text-primary">PROTOCOL</span></span>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                isActive 
                  ? "bg-primary/10 text-primary shadow-[inset_0_0_10px_rgba(0,245,212,0.1)]" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary opacity-0 group-[.active]:opacity-100 transition-opacity" />
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border/50">
          <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10" onClick={logout}>
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-6 bg-background/80 backdrop-blur-md border-b border-border/50 sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setIsMobileMenuOpen(true)}>
              <Menu className="w-6 h-6" />
            </Button>
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/50 border border-border/50 text-xs font-medium text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              Network Status: <span className="text-primary uppercase tracking-wider">Mainnet Alpha</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button variant="outline" className="hidden sm:flex gap-2 rounded-full border-primary/30 hover:border-primary hover:bg-primary/5 transition-all">
              <Wallet className="w-4 h-4 text-primary" />
              <span className="text-sm font-mono">0x4f...a2d1</span>
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full ring-1 ring-border/50 hover:ring-primary/50 transition-all p-0">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={user?.metadata?.avatar} />
                    <AvatarFallback className="bg-secondary text-secondary-foreground">{user?.displayName?.[0] || 'U'}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-card border-border shadow-2xl">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="font-bold">{user?.displayName}</span>
                    <span className="text-xs text-muted-foreground font-mono">{user?.email}</span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="gap-2 cursor-pointer">
                  <Settings className="w-4 h-4" /> Profile Settings
                </DropdownMenuItem>
                <DropdownMenuItem className="gap-2 cursor-pointer text-destructive focus:text-destructive" onClick={logout}>
                  <LogOut className="w-4 h-4" /> Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main Viewport */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-10 scroll-smooth">
          <div className="max-w-7xl mx-auto animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setIsMobileMenuOpen(false)} />
          <aside className="fixed inset-y-0 left-0 w-72 bg-sidebar border-r border-border shadow-2xl flex flex-col p-6 animate-in slide-in-from-left duration-300">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-primary" />
                <span className="font-display font-bold text-xl">NWU PROTOCOL</span>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(false)}>
                <X className="w-6 h-6" />
              </Button>
            </div>
            <nav className="space-y-4">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) => cn(
                    "flex items-center gap-3 p-3 rounded-lg",
                    isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </div>
  );
}

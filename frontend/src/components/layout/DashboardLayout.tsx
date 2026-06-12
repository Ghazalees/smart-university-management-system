import { useSelector, useDispatch } from "react-redux";
import {
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Avatar,
} from "@nextui-org/react";
import { navConfig } from "../../pages/Dashboard/navconfig";
import { Sidebar } from "./Sidebar";
import { logout } from "../../states/authSlice";
import { ThemeToggle } from "../ThemeToggle";
import { motion } from "framer-motion";
import { LogOut, User } from "lucide-react";

export const DashboardLayout = ({ children }) => {
  const { role, user } = useSelector((state: any) => state.auth);
  const currentNav = navConfig[role as keyof typeof navConfig] || [];
  const dispatch = useDispatch();

  return (
    <div className="flex h-screen bg-background">
      <Sidebar navItems={currentNav} />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <Navbar className="border-b border-divider" maxWidth="full">
          <NavbarBrand>
            <p className="font-bold text-inherit uppercase">{role}</p>
          </NavbarBrand>

          <NavbarContent justify="end" className="p-4">
            <NavbarItem>
              <ThemeToggle />
            </NavbarItem>
            <NavbarItem>
              <Dropdown
                placement="bottom-end"
                className="bg-white dark:bg-black"
              >
                <DropdownTrigger>
                  <Avatar
                    isBordered
                    icon={<User />}
                    as="button"
                    className="transition-transform"
                    // color="primary"
                    // name={user?.name || "User"}
                    size="sm"
                    src={user?.avatarUrl}
                  />
                </DropdownTrigger>
                <DropdownMenu
                  aria-label="Profile Actions"
                  variant="flat"
                  className="bg-default p-2 rounded-xl border border-divider shadow-medium"
                >
                  <DropdownItem
                    key="profile"
                    className="h-14 gap-2 hover:border-none"
                  >
                    <p className="font-semibold">Signed in as</p>
                    <p className="text-small text-default-500">{user?.email}</p>
                  </DropdownItem>

                  <DropdownItem
                    key="logout"
                    color="danger"
                    className="text-danger hover:cursor-pointer"
                    startContent={<LogOut size={16} />}
                    onClick={() => {
                      dispatch(logout());
                    }}
                  >
                    Log Out
                  </DropdownItem>
                </DropdownMenu>
              </Dropdown>
            </NavbarItem>
          </NavbarContent>
        </Navbar>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};

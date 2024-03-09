const pillColors = {
  blue: "bg-blue-500 border-blue-500 text-white",
  green: "bg-green-500 border-green-500 text-white",
  red: "bg-red-500 border-red-500 text-white",
  yellow: "bg-yellow-500 border-yellow-500 text-white",
  gray: "bg-gray-500 border-gray-500 text-white",
  indigo: "bg-indigo-500 border-indigo-500 text-white",
  purple: "bg-purple-500 border-purple-500 text-white",
  pink: "bg-pink-500 border-pink-500 text-white",
};

export const Pill: React.FC<
  React.PropsWithChildren<
    {
      color: keyof typeof pillColors;
    } & React.HTMLAttributes<HTMLSpanElement>
  >
> = ({ children, color, ...props }) => (
  <span
    className={`py-1 px-2 shadow-md no-underline rounded-full font-mono text-sm mx-2 ${pillColors[color]} transition-colors duration-200`}
    {...props}
  >
    {children}
  </span>
);

export const handle = async ({ event, resolve }) => {
  return resolve(event, {
    preload: ({ type }) => type === "font" || type === "js" || type === "css",
  });
};

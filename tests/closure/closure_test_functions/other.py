"""Other functions used in the main closure test functions."""


def imported_fn() -> str:
    return "Hello, world!"


def imported_sub_fn() -> str:
    return imported_fn()


class ImportedClass:
    def __call__(self) -> str:
        return "Hello, world!"


class FnInsideClass:
    def __call__(self) -> str:
        return imported_fn()


class SubFnInsideClass:
    def __call__(self) -> str:
        return imported_sub_fn()


class SelfFnClass:
    def fn(self) -> str:
        return "Hello, world!"

    def __call__(self) -> str:
        return self.fn()

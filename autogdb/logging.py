class Logger:
    def __init__(self) -> None:
        self.SUCCESS_PREFIX = "\033[92m[*]\033[0m"
        self.SUCCESS_TEXT_COLOR = "\033[94m"

        self.INFO_PREFIX = "\033[33m[info]\033[0m"
        self.INFO_TEXT_COLOR = "\033[93m"

        self.FAILURE_PREFIX = "\033[90m[!]\033[0m"
        self.FAILURE_TEXT_COLOR = "\033[91m"

        self.RESET_COLOR = "\033[0m"

    def info(self,message,PrevReturn=False):
        if not PrevReturn:
            print(f"    {self.INFO_PREFIX} {self.INFO_TEXT_COLOR}{message}{self.RESET_COLOR}")
        else:
            print(f"    \n\n{self.INFO_PREFIX} {self.INFO_TEXT_COLOR}{message}{self.RESET_COLOR}")
        

    def success(self,message,PrevReturn=False):
        if not PrevReturn:
            print(f"    {self.SUCCESS_PREFIX} {self.SUCCESS_TEXT_COLOR}{message}{self.RESET_COLOR}")
        else:
            print(f"    \n\n{self.SUCCESS_PREFIX} {self.SUCCESS_TEXT_COLOR}{message}{self.RESET_COLOR}")

    def fail(self,message):
        print(f"    {self.FAILURE_PREFIX} {self.FAILURE_TEXT_COLOR}{message}{self.RESET_COLOR}")
        exit(0)
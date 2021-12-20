import Client


def main():
    team_name = input()
    client = Client(team_name)
    client.start_client()


if __name__ == '__main__':
    main()

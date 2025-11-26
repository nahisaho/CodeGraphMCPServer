/**
 * Sample TypeScript project for testing.
 * A simple user management module.
 */

export interface User {
    id: string;
    name: string;
    email: string;
    createdAt: Date;
}

export interface UserRepository {
    findById(id: string): Promise<User | null>;
    findByEmail(email: string): Promise<User | null>;
    save(user: User): Promise<void>;
    delete(id: string): Promise<boolean>;
}

export class InMemoryUserRepository implements UserRepository {
    private users: Map<string, User> = new Map();

    async findById(id: string): Promise<User | null> {
        return this.users.get(id) || null;
    }

    async findByEmail(email: string): Promise<User | null> {
        for (const user of this.users.values()) {
            if (user.email === email) {
                return user;
            }
        }
        return null;
    }

    async save(user: User): Promise<void> {
        this.users.set(user.id, user);
    }

    async delete(id: string): Promise<boolean> {
        return this.users.delete(id);
    }
}

export class UserService {
    constructor(private repository: UserRepository) {}

    async getUser(id: string): Promise<User | null> {
        return this.repository.findById(id);
    }

    async createUser(name: string, email: string): Promise<User> {
        const existingUser = await this.repository.findByEmail(email);
        if (existingUser) {
            throw new Error(`User with email ${email} already exists`);
        }

        const user: User = {
            id: crypto.randomUUID(),
            name,
            email,
            createdAt: new Date(),
        };

        await this.repository.save(user);
        return user;
    }

    async deleteUser(id: string): Promise<boolean> {
        return this.repository.delete(id);
    }
}
